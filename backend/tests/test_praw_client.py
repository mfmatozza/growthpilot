import pytest

from app.services.reddit.base import RedditError
from app.services.reddit.praw_client import PrawRedditClient


def test_missing_credentials_raises_immediately():
    with pytest.raises(RedditError, match="REDDIT_CLIENT_ID"):
        PrawRedditClient(client_id="", client_secret="")
