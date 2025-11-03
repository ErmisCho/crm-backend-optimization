import time
import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from django.test import Client
from datetime import datetime


class Command(BaseCommand):
    help = "Benchmark list view with common scenarios and save results to file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--repeat",
            type=int,
            default=5,
            help="Number of repetitions per scenario (default: 5)"
        )

    def handle(self, *args, **options):
        repeat = options["repeat"]
        client = Client()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        results = []

        def run(label, url):
            times = []
            for _ in range(repeat):
                t0 = time.perf_counter()
                r = client.get(url)
                dt = (time.perf_counter() - t0) * 1000
                times.append(dt)
            avg_dt = sum(times) / len(times)
            best_dt = min(times)
            worst_dt = max(times)
            size = len(r.content)
            self.stdout.write(
                f"{label:32s} avg={avg_dt:7.1f} ms  best={best_dt:7.1f} ms  worst={worst_dt:7.1f} ms  status={r.status_code} size={size:,} bytes"
            )
            results.append([
                timestamp, label, url, repeat, r.status_code,
                f"{avg_dt:.1f}", f"{best_dt:.1f}", f"{worst_dt:.1f}", size
            ])

        # test scenarios
        run("Initial page", "/api/users/?page=1&page_size=50")
        run("Filter last_name=smith", "/api/users/?last_name=smith&page_size=50")
        run("Sort by points desc",
            "/api/users/?order_by=-relationship__points&page_size=50")
        run("City=Vienna + paginate", "/api/users/?city=Vienna&page=3&page_size=50")

        # write results
        out_file = Path("reports/benchmarks.csv")
        out_file.parent.mkdir(exist_ok=True)
        new_file = not out_file.exists()

        with open(out_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if new_file:
                writer.writerow([
                    "timestamp", "label", "url", "repeat", "status",
                    "avg_ms", "best_ms", "worst_ms", "response_size"
                ])
            writer.writerows(results)

        self.stdout.write(self.style.SUCCESS(
            f"Saved {len(results)} results to {out_file.resolve()}"
        ))
