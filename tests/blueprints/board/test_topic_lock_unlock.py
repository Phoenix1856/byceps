"""
:Copyright: 2006-2018 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from byceps.services.board import topic_service as board_topic_service

from .topic_moderation_base import AbstractTopicModerationTest


class TopicLockTest(AbstractTopicModerationTest):

    def setUp(self):
        super().setUp()

        self.setup_admin_with_permission('board_topic.lock')

        self.category_id = self.create_category(1).id

    def test_lock_topic(self):
        topic_before = self.create_topic(self.category_id, self.user.id, 1)

        assert_topic_is_not_locked(topic_before)

        url = '/board/topics/{}/flags/locked'.format(topic_before.id)
        with self.client(user_id=self.admin.id) as client:
            response = client.post(url)

        assert response.status_code == 204
        topic_afterwards = self.find_topic(topic_before.id)
        assert_topic_is_locked(topic_afterwards, self.admin.id)

    def test_unlock_topic(self):
        topic_before = self.create_topic(self.category_id, self.user.id, 1)
        board_topic_service.lock_topic(topic_before, self.admin.id)

        assert_topic_is_locked(topic_before, self.admin.id)

        url = '/board/topics/{}/flags/locked'.format(topic_before.id)
        with self.client(user_id=self.admin.id) as client:
            response = client.delete(url)

        assert response.status_code == 204
        topic_afterwards = self.find_topic(topic_before.id)
        assert_topic_is_not_locked(topic_afterwards)


def assert_topic_is_locked(topic, moderator_id):
    assert topic.locked
    assert topic.locked_at is not None
    assert topic.locked_by_id == moderator_id


def assert_topic_is_not_locked(topic):
    assert not topic.locked
    assert topic.locked_at is None
    assert topic.locked_by_id is None
