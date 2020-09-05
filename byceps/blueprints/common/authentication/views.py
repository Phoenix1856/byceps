"""
byceps.blueprints.common.authentication.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from typing import Optional

from flask import abort, g, request, url_for

from ....config import get_app_mode
from ....services.authentication.exceptions import AuthenticationFailed
from ....services.authentication import service as authentication_service
from ....services.authentication.password import service as password_service
from ....services.authentication.password import (
    reset_service as password_reset_service,
)
from ....services.authentication.session import service as session_service
from ....services.consent import (
    consent_service,
    subject_service as consent_subject_service,
)
from ....services.email import service as email_service
from ....services.email.transfer.models import Sender
from ....services.site import service as site_service
from ....services.user import service as user_service
from ....services.verification_token import (
    service as verification_token_service,
)
from ....services.verification_token.models import Token as VerificationToken
from ....typing import UserID
from ....util.framework.blueprint import create_blueprint
from ....util.framework.flash import flash_error, flash_notice, flash_success
from ....util.framework.templating import templated
from ....util.views import redirect_to, respond_no_content

from ...admin.core.authorization import AdminPermission

from .forms import (
    LoginForm,
    RequestPasswordResetForm,
    ResetPasswordForm,
    UpdatePasswordForm,
)
from . import service, session as user_session


blueprint = create_blueprint('authentication', __name__)


# -------------------------------------------------------------------- #
# log in/out


@blueprint.route('/login')
@templated
def login_form():
    """Show login form."""
    logged_in = g.current_user.is_active
    if logged_in:
        flash_notice(
            f'Du bist bereits als Benutzer "{g.current_user.screen_name}" '
            'angemeldet.'
        )

    in_admin_mode = get_app_mode().is_admin()

    if not _is_login_enabled(in_admin_mode):
        return {
            'login_enabled': False,
        }

    form = LoginForm()
    user_account_creation_enabled = _is_user_account_creation_enabled(
        in_admin_mode
    )

    return {
        'login_enabled': True,
        'logged_in': logged_in,
        'form': form,
        'user_account_creation_enabled': user_account_creation_enabled,
    }


@blueprint.route('/login', methods=['POST'])
@respond_no_content
def login():
    """Allow the user to authenticate with e-mail address and password."""
    if g.current_user.is_active:
        return

    in_admin_mode = get_app_mode().is_admin()

    if not _is_login_enabled(in_admin_mode):
        abort(403, 'Log in to this site is generally disabled.')

    form = LoginForm(request.form)

    screen_name = form.screen_name.data.strip()
    password = form.password.data
    permanent = form.permanent.data
    if not all([screen_name, password]):
        abort(403)

    try:
        user = authentication_service.authenticate(screen_name, password)
    except AuthenticationFailed:
        abort(403)

    if in_admin_mode:
        _require_admin_access_permission(user.id)

    if not in_admin_mode:
        required_consent_subject_ids = _get_required_consent_subject_ids()
        if _is_consent_required(user.id, required_consent_subject_ids):
            verification_token = verification_token_service.create_for_terms_consent(
                user.id
            )

            consent_form_url = url_for(
                'consent.consent_form', token=verification_token.token
            )

            return [('Location', consent_form_url)]

    # Authorization succeeded.

    session_token = session_service.get_session_token(user.id)

    session_service.record_recent_login(user.id)
    service.create_login_event(user.id, request.remote_addr)

    user_session.start(user.id, session_token.token, permanent=permanent)
    flash_success(f'Erfolgreich eingeloggt als {user.screen_name}.')


def _require_admin_access_permission(user_id: UserID) -> None:
    permissions = service.get_permissions_for_user(user_id)
    if AdminPermission.access not in permissions:
        # The user lacks the admin access permission which is required
        # to enter the admin area.
        abort(403)


def _get_required_consent_subject_ids():
    subjects_required_for_brand = consent_subject_service.get_subjects_required_for_brand(
        g.brand_id
    )
    return {subject.id for subject in subjects_required_for_brand}


def _is_consent_required(user_id, subject_ids):
    return not consent_service.has_user_consented_to_all_subjects(
        user_id, subject_ids
    )


@blueprint.route('/logout', methods=['POST'])
@respond_no_content
def logout():
    """Log out user by deleting the corresponding cookie."""
    user_session.end()
    flash_success('Erfolgreich ausgeloggt.')


# -------------------------------------------------------------------- #
# password update


@blueprint.route('/password/update')
@templated
def password_update_form(erroneous_form=None):
    """Show a form to update the current user's password."""
    _get_current_user_or_404()

    form = erroneous_form if erroneous_form else UpdatePasswordForm()

    return {'form': form}


@blueprint.route('/password', methods=['POST'])
def password_update():
    """Update the current user's password."""
    user = _get_current_user_or_404()

    form = UpdatePasswordForm(request.form)

    if not form.validate():
        return password_update_form(form)

    password = form.new_password.data

    password_service.update_password_hash(user.id, password, user.id)

    flash_success('Dein Passwort wurde geändert. Bitte melde dich erneut an.')
    return redirect_to('.login_form')


# -------------------------------------------------------------------- #
# password reset


@blueprint.route('/password/reset/request')
@templated
def request_password_reset_form(erroneous_form=None):
    """Show a form to request a password reset."""
    form = erroneous_form if erroneous_form else RequestPasswordResetForm()

    return {'form': form}


@blueprint.route('/password/reset/request', methods=['POST'])
def request_password_reset():
    """Request a password reset."""
    form = RequestPasswordResetForm(request.form)
    if not form.validate():
        return request_password_reset_form(form)

    screen_name = form.screen_name.data.strip()
    user = user_service.find_user_by_screen_name(
        screen_name, case_insensitive=True
    )

    if (user is None) or user.deleted:
        flash_error(f'Der Benutzername "{screen_name}" ist unbekannt.')
        return request_password_reset_form(form)

    if user.email_address is None:
        flash_error(
            f'Für das Benutzerkonto "{screen_name}" ist keine E-Mail-Adresse hinterlegt.'
        )
        return request_password_reset_form(form)

    if not user.email_address_verified:
        flash_error(
            f'Die E-Mail-Adresse für das Benutzerkonto "{screen_name}" '
            'wurde noch nicht bestätigt.'
        )
        return redirect_to('user_email_address.request_confirmation_email')

    if user.suspended:
        flash_error(f'Das Benutzerkonto "{screen_name}" ist gesperrt.')
        return request_password_reset_form(form)

    sender = _get_sender()

    password_reset_service.prepare_password_reset(
        user, request.url_root, sender=sender
    )

    flash_success(
        'Ein Link zum Setzen eines neuen Passworts '
        f'für den Benutzernamen "{user.screen_name}" '
        'wurde an die hinterlegte E-Mail-Adresse versendet.'
    )
    return request_password_reset_form()


def _get_sender() -> Optional[Sender]:
    if not get_app_mode().is_site():
        return None

    site = site_service.get_site(g.site_id)
    email_config = email_service.get_config(site.email_config_id)
    return email_config.sender


@blueprint.route('/password/reset/token/<token>')
@templated
def password_reset_form(token, erroneous_form=None):
    """Show a form to reset the current user's password."""
    _verify_password_reset_token(token)

    form = erroneous_form if erroneous_form else ResetPasswordForm()

    return {
        'form': form,
        'token': token,
    }


@blueprint.route('/password/reset/token/<token>', methods=['POST'])
def password_reset(token):
    """Reset the current user's password."""
    verification_token = _verify_password_reset_token(token)

    form = ResetPasswordForm(request.form)
    if not form.validate():
        return password_reset_form(token, form)

    password = form.new_password.data

    password_reset_service.reset_password(verification_token, password)

    flash_success('Das Passwort wurde geändert.')
    return redirect_to('.login_form')


def _verify_password_reset_token(token: str) -> VerificationToken:
    verification_token = verification_token_service.find_for_password_reset_by_token(
        token
    )

    if not _is_verification_token_valid(verification_token):
        flash_error(
            'Es wurde kein gültiges Token angegeben. '
            'Ein Token ist nur 24 Stunden lang gültig.'
        )
        abort(404)

    user = user_service.find_active_user(verification_token.user_id)
    if user is None:
        flash_error('Es wurde kein gültiges Token angegeben.')
        abort(404)

    return verification_token


def _is_verification_token_valid(token: Optional[VerificationToken]) -> bool:
    return (token is not None) and not token.is_expired


# -------------------------------------------------------------------- #
# helpers


def _is_user_account_creation_enabled(in_admin_mode):
    if in_admin_mode:
        return False

    site = _get_site()
    return site.user_account_creation_enabled


def _is_login_enabled(in_admin_mode):
    if in_admin_mode:
        return True

    site = _get_site()
    return site.login_enabled


def _get_site():
    return site_service.get_site(g.site_id)


def _get_current_user_or_404():
    user = g.current_user
    if not user.is_active:
        abort(404)

    return user
