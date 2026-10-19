"""Database failure recovery without a live database or browser."""
import unittest
from unittest.mock import MagicMock, call, patch

import psycopg2

import cloud_scrape_details as scraper


class DescriptionRecoveryTests(unittest.TestCase):
    def test_reconnects_and_retries_original_jd(self):
        for error_type in (
            psycopg2.DatabaseError, psycopg2.OperationalError,
            psycopg2.InterfaceError,
        ):
            with self.subTest(error_type=error_type):
                broken, healthy = MagicMock(), MagicMock()
                broken.cursor.return_value.execute.side_effect = error_type(
                    "Can't assign requested address"
                )
                with patch.object(scraper, 'get_connection', side_effect=[broken, healthy]), \
                     patch.object(scraper.time, 'sleep'):
                    scraper.save_description('job-link', 'original JD')

                broken.close.assert_called_once()
                broken.commit.assert_not_called()
                healthy.close.assert_called_once()
                healthy.commit.assert_called_once()
                args = healthy.cursor.return_value.execute.call_args.args
                self.assertEqual(args[1], ('original JD', 'job-link'))

    def test_retries_connection_creation_failure(self):
        healthy = MagicMock()
        with patch.object(scraper, 'get_connection', side_effect=[
            psycopg2.OperationalError('connection unavailable'), healthy,
        ]) as connect, patch.object(scraper.time, 'sleep'):
            scraper.save_description('job-link', 'JD')
        self.assertEqual(connect.call_count, 2)
        healthy.close.assert_called_once()
        healthy.commit.assert_called_once()

    def test_stops_after_three_attempts_and_closes_connections(self):
        connections = [MagicMock() for _ in range(3)]
        for conn in connections:
            conn.cursor.return_value.execute.side_effect = psycopg2.OperationalError(
                'SSL SYSCALL error: EOF detected'
            )
        with patch.object(scraper, 'get_connection', side_effect=connections) as connect, \
             patch.object(scraper.time, 'sleep') as sleep:
            with self.assertRaises(psycopg2.OperationalError):
                scraper.save_description('job-link', 'JD')
        self.assertEqual(connect.call_count, 3)
        self.assertEqual(sleep.call_args_list, [call(1), call(2)])
        for conn in connections:
            conn.close.assert_called_once()

    def test_does_not_retry_sql_errors(self):
        for error in (psycopg2.ProgrammingError('bad SQL'),
                      psycopg2.IntegrityError('constraint violation')):
            with self.subTest(error=error):
                conn = MagicMock()
                conn.cursor.return_value.execute.side_effect = error
                with patch.object(scraper, 'get_connection', return_value=conn) as connect, \
                     patch.object(scraper.time, 'sleep') as sleep:
                    with self.assertRaises(type(error)):
                        scraper.save_description('job-link', 'JD')
                connect.assert_called_once()
                sleep.assert_not_called()
                conn.close.assert_called_once()

    def test_does_not_retry_server_errors_with_sqlstate(self):
        class ServerError(psycopg2.OperationalError):
            pgcode = '57014'

        conn = MagicMock()
        conn.cursor.return_value.execute.side_effect = ServerError('query cancelled')
        with patch.object(scraper, 'get_connection', return_value=conn) as connect:
            with self.assertRaises(ServerError):
                scraper.save_description('job-link', 'JD')
        connect.assert_called_once()
        conn.close.assert_called_once()


class PipelineRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        playwright = MagicMock()
        page = playwright.__enter__.return_value.chromium.launch.return_value.new_context.return_value.new_page.return_value
        page.locator.return_value.count.return_value = 1
        page.locator.return_value.first.inner_text.return_value = 'original JD'
        self.page = page
        def start_browser():
            self.conn.close.assert_called_once()
            return playwright

        replacements = {
            'get_connection': MagicMock(return_value=self.conn),
            'get_pending_jobs': MagicMock(return_value=[(1, 'job-link', 'Job title')]),
            'sync_playwright': MagicMock(side_effect=start_browser),
            'Stealth': MagicMock(),
            'load_cookies': MagicMock(),
            'save_cookies': MagicMock(),
            'get_browser_config': MagicMock(return_value={
                'user_agent': 'test', 'extra_http_headers': {},
            }),
            'human_like_mouse': MagicMock(),
            'human_like_scroll': MagicMock(),
            'smart_delay': MagicMock(),
            'solve_cloudflare_turnstile': MagicMock(return_value=True),
        }
        self.patches = patch.multiple(scraper, **replacements)
        self.patches.start()
        self.addCleanup(self.patches.stop)
        sleep = patch.object(scraper.time, 'sleep')
        sleep.start()
        self.addCleanup(sleep.stop)

    def test_database_failure_does_not_attempt_to_write_error(self):
        with patch.object(scraper, 'save_description', side_effect=
                          psycopg2.DatabaseError('connection lost')) as save:
            with self.assertRaises(psycopg2.DatabaseError):
                scraper.run()
        save.assert_called_once_with('job-link', 'original JD')
        self.conn.close.assert_called_once()

    def test_scrape_failure_leaves_job_pending(self):
        self.page.goto.side_effect = [None, RuntimeError('navigation failed')]
        with patch.object(scraper, 'save_description') as save:
            scraper.run()
        save.assert_not_called()
        self.conn.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
