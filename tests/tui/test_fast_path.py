def test_main_screen_when_app_starts(snap_compare):
    assert snap_compare()


def test_open_help(snap_compare):
    assert snap_compare(press=["?"])


def test_show_url_open_dialog_and_hit_enter(snap_compare):
    # Hit enter without entering anything because input has flickering cursor
    # and test will be flaky.
    # So we hit enter, at least we can see error "wrong url"
    assert snap_compare(press=["f1", "1", "enter"])


def test_show_file_open_dialog(snap_compare):
    assert snap_compare(press=["f1", "2"])


def test_show_couchdb_url_open_dialog(snap_compare):
    assert snap_compare(press=["f1", "3", "enter"])


def test_open_file_in_right_panel(snap_compare):
    assert snap_compare(press=["f2", "2", "down", "enter", "tab", "tab"])


def test_make_diff_of_couchdb_revisions(snap_compare, couchdb_server, document_url):
    assert snap_compare(
        press=[
            "f1",
            "3",
            *list(couchdb_server.url_for(document_url)),
            "enter",
            "s",
            "[",
            "tab",
        ]
    )
