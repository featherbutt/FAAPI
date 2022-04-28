from datetime import datetime
from json import loads
from os import environ

from pytest import fixture
from pytest import raises
from requests.cookies import RequestsCookieJar

import faapi
from faapi import Comment
from faapi import FAAPI
from faapi import SubmissionPartial
from faapi.exceptions import Unauthorized
from faapi.parse import username_url
from test_parse import clean_html


@fixture
def data() -> dict:
    return loads(environ["TEST_DATA"])


@fixture
def cookies(data: dict) -> RequestsCookieJar:
    return data["cookies"]


@fixture
def submission_test_data() -> dict:
    return loads(environ["TEST_SUBMISSION"])


@fixture
def journal_test_data() -> dict:
    return loads(environ["TEST_JOURNAL"])


def test_robots(cookies: RequestsCookieJar):
    api: FAAPI = FAAPI(cookies)
    assert getattr(api.robots, "default_entry") is not None
    assert api.crawl_delay >= 1
    assert api.check_path("/login")
    assert api.check_path("/view")
    assert api.check_path("/journal")
    assert api.check_path("/user")
    assert api.check_path("/gallery")
    assert api.check_path("/scraps")
    assert api.check_path("/favorite")
    assert api.check_path("/journals")
    assert api.check_path("/watchlist/to")
    assert api.check_path("/watchlist/by")


def test_login(cookies: RequestsCookieJar):
    api: FAAPI = FAAPI(cookies)
    assert api.login_status

    api.load_cookies([{"name": "a", "value": "1"}])
    with raises(Unauthorized):
        api.me()


# noinspection DuplicatedCode
def test_submission(cookies: RequestsCookieJar, submission_test_data: dict):
    api: FAAPI = FAAPI(cookies)

    submission, _ = api.submission(submission_test_data["id"], get_file=False)
    submission_dict = dict(submission)

    assert submission.id == submission_dict["id"] == submission_test_data["id"]
    assert submission.title == submission_dict["title"] == submission_test_data["title"]
    assert submission.author.name == submission_dict["author"]["name"] == submission_test_data["author"]["name"]
    assert submission.author.user_icon_url == submission_dict["author"]["user_icon_url"] != ""
    assert submission.date == submission_dict["date"] == datetime.fromisoformat(submission_test_data["date"])
    assert submission.tags == submission_dict["tags"] == submission_test_data["tags"]
    assert submission.category == submission_dict["category"] == submission_test_data["category"]
    assert submission.species == submission_dict["species"] == submission_test_data["species"]
    assert submission.gender == submission_dict["gender"] == submission_test_data["gender"]
    assert submission.rating == submission_dict["rating"] == submission_test_data["rating"]
    assert submission.stats.views == submission_dict["stats"]["views"]
    assert submission.stats.views >= submission_test_data["stats"]["views"]
    assert submission.stats.comments == submission_dict["stats"]["comments"]
    assert submission.stats.comments >= submission_test_data["stats"]["comments"]
    assert submission.stats.favorites == submission_dict["stats"]["favorites"]
    assert submission.stats.favorites >= submission_test_data["stats"]["favorites"]
    assert submission.type == submission_dict["type"] == submission_test_data["type"]
    assert submission.mentions == submission_dict["mentions"] == submission_test_data["mentions"]
    assert submission.folder == submission_dict["folder"] == submission_test_data["folder"]
    assert submission.file_url == submission_dict["file_url"] != ""
    assert submission.thumbnail_url == submission_dict["thumbnail_url"] != ""
    assert submission.prev == submission_dict["prev"] == submission_test_data["prev"]
    assert submission.next == submission_dict["next"] == submission_test_data["next"]
    assert clean_html(submission.description) == clean_html(submission_dict["description"]) == \
           clean_html(submission_test_data["description"])

    assert len(faapi.comment.flatten_comments(submission.comments)) == submission.stats.comments

    comments: dict[int, Comment] = {c.id: c for c in faapi.comment.flatten_comments(submission.comments)}

    for comment in comments.values():
        assert comment.reply_to is None or isinstance(comment.reply_to, Comment)

        if comment.reply_to:
            assert comment.reply_to.id in comments
            assert comment in comments[comment.reply_to.id].replies

        if comment.replies:
            for reply in comment.replies:
                assert reply.reply_to == comment


# noinspection DuplicatedCode
def test_journal(cookies: RequestsCookieJar, journal_test_data: dict):
    api: FAAPI = FAAPI(cookies)

    journal = api.journal(journal_test_data["id"])
    journal_dict = dict(journal)

    assert journal.id == journal_dict["id"] == journal_test_data["id"]
    assert journal.title == journal_dict["title"] == journal_test_data["title"]
    assert journal.author.name == journal_dict["author"]["name"] == journal_test_data["author"]["name"]
    assert journal.author.join_date == journal_dict["author"]["join_date"] == \
           datetime.fromisoformat(journal_test_data["author"]["join_date"])
    assert journal.author.user_icon_url == journal_dict["author"]["user_icon_url"] != ""
    assert journal.date == journal_dict["date"] == datetime.fromisoformat(journal_test_data["date"])
    assert journal.stats.comments == journal_dict["stats"]["comments"] >= journal_test_data["stats"]["comments"]
    assert journal.mentions == journal_dict["mentions"] == journal_test_data["mentions"]
    assert clean_html(journal.content) == clean_html(journal_dict["content"]) == \
           clean_html(journal_test_data["content"])

    assert len(faapi.comment.flatten_comments(journal.comments)) == journal.stats.comments

    comments: dict[int, Comment] = {c.id: c for c in faapi.comment.flatten_comments(journal.comments)}

    for comment in comments.values():
        assert comment.reply_to is None or isinstance(comment.reply_to, Comment)

        if comment.reply_to:
            assert comment.reply_to.id in comments
            assert comment in comments[comment.reply_to.id].replies

        if comment.replies:
            for reply in comment.replies:
                assert reply.reply_to == comment


# noinspection DuplicatedCode
def test_gallery(cookies: RequestsCookieJar, data: dict):
    api: FAAPI = FAAPI(cookies)

    ss, p = [], 1

    while p:
        ss_, p_ = api.gallery(data["gallery"]["user"], p)
        assert isinstance(ss, list)
        assert all(isinstance(s, SubmissionPartial) for s in ss)
        assert isinstance(p_, int)
        assert p_ > p or p_ == 0
        assert len(ss) or p == 1

        ss.extend(ss_)
        p = p_

    assert len(ss) >= data["gallery"]["length"]

    for submission in ss:
        assert submission.id > 0
        assert submission.type != ""
        assert submission.rating != ""
        assert submission.thumbnail_url != ""
        assert submission.author.name_url == username_url(data["gallery"]["user"])


# noinspection DuplicatedCode
def test_scraps(cookies: RequestsCookieJar, data: dict):
    api: FAAPI = FAAPI(cookies)

    ss, p = [], 1

    while p:
        ss_, p_ = api.scraps(data["scraps"]["user"], p)
        assert isinstance(ss, list)
        assert all(isinstance(s, SubmissionPartial) for s in ss)
        assert isinstance(p_, int)
        assert p_ > p or p_ == 0
        assert len(ss) or p == 1

        ss.extend(ss_)
        p = p_

    assert len(ss) >= data["scraps"]["length"]

    for submission in ss:
        assert submission.id > 0
        assert submission.type != ""
        assert submission.rating != ""
        assert submission.thumbnail_url != ""
        assert submission.author.name_url == username_url(data["gallery"]["user"])