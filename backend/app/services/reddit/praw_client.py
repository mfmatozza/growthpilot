import praw
import prawcore

from app.core.config import get_settings
from app.services.reddit.base import RedditError, RedditMonitorClient, RedditThread
from app.services.retry import external_api_retry

_RETRYABLE = (prawcore.exceptions.RequestException, prawcore.exceptions.ResponseException)


class PrawRedditClient(RedditMonitorClient):
    def __init__(
        self, client_id: str | None = None, client_secret: str | None = None, user_agent: str | None = None
    ) -> None:
        settings = get_settings()
        self._client_id = client_id or settings.reddit_client_id
        self._client_secret = client_secret or settings.reddit_client_secret
        self._user_agent = user_agent or settings.reddit_user_agent
        if not self._client_id or not self._client_secret:
            raise RedditError("REDDIT_CLIENT_ID/REDDIT_CLIENT_SECRET are not set.")
        # Read-only app-only auth — no username/password needed since this
        # only ever reads public posts, never posts on the user's behalf
        # (draft replies are reviewed and posted by hand, see the brief).
        self._reddit = praw.Reddit(
            client_id=self._client_id, client_secret=self._client_secret, user_agent=self._user_agent
        )

    @external_api_retry(_RETRYABLE)
    def search(self, subreddit: str, query: str, limit: int = 5) -> list[RedditThread]:
        try:
            results = self._reddit.subreddit(subreddit).search(query, sort="new", time_filter="month", limit=limit)
            return [
                RedditThread(
                    url=f"https://www.reddit.com{submission.permalink}",
                    subreddit=subreddit,
                    title=submission.title,
                    body=(submission.selftext or "")[:2000],
                )
                for submission in results
            ]
        except (prawcore.exceptions.RequestException, prawcore.exceptions.ResponseException):
            raise
        except Exception as exc:
            raise RedditError(f"Reddit search failed for r/{subreddit} ({query!r}): {exc}") from exc
