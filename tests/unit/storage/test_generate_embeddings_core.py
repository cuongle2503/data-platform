from unittest.mock import MagicMock, patch

from idp.storage.generate_indicator_embeddings import (
    _process_batch,
    generate_indicator_embeddings,
    run,
)


def test_process_batch_success():
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur
    client = MagicMock()
    client.generate_embeddings_batch.return_value = [[0.1, 0.2], [0.3, 0.4]]

    created = _process_batch(
        conn, client, ["text1", "text2"], ["ref1", "ref2"], "economic_indicator"
    )

    assert created == 2
    assert cur.execute.call_count == 2
    conn.commit.assert_called_once()


def test_process_batch_api_failure():
    conn = MagicMock()
    client = MagicMock()
    client.generate_embeddings_batch.side_effect = Exception("API Error")

    created = _process_batch(conn, client, ["text1"], ["ref1"], "economic_indicator")

    assert created == 0


def test_process_batch_db_failure():
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur
    cur.execute.side_effect = Exception("DB Error")

    client = MagicMock()
    client.generate_embeddings_batch.return_value = [[0.1, 0.2]]

    created = _process_batch(conn, client, ["text1"], ["ref1"], "economic_indicator")

    assert created == 0
    conn.commit.assert_called_once()


@patch("idp.storage.generate_indicator_embeddings.get_existing_ref_ids")
@patch("idp.storage.generate_indicator_embeddings._process_batch")
def test_generate_indicator_embeddings(mock_process, mock_get_existing):
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur

    # 3 indicators total
    cur.fetchall.return_value = [
        ("NY.GDP", "GDP", "cat1", "unit1", "desc1"),
        ("SP.POP", "Pop", "cat2", "unit2", "desc2"),
        ("EN.ATM", "Env", "cat3", "unit3", "desc3"),
    ]

    # 1 already exists
    mock_get_existing.return_value = {"NY.GDP"}
    mock_process.return_value = 2

    client = MagicMock()

    # Run with batch size 1 to force multiple batches
    created = generate_indicator_embeddings(conn, client, batch_size=1)

    assert created == 4  # 2 + 2 from process_batch returning 2 twice
    assert mock_process.call_count == 2


@patch("idp.common.config.get_settings")
@patch("idp.storage.generate_indicator_embeddings.GeminiEmbeddingsClient")
@patch("idp.storage.generate_indicator_embeddings.psycopg2.connect")
@patch("idp.storage.generate_indicator_embeddings.generate_indicator_embeddings")
def test_run_success(mock_gen, mock_connect, mock_client, mock_settings):
    mock_pg = MagicMock()
    mock_pg.database_url = "postgres://url"
    mock_settings.return_value.postgres = mock_pg

    run()

    mock_connect.assert_called_once()
    mock_gen.assert_called_once()
