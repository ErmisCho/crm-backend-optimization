import csv
import io
import random
import time
from pathlib import Path
from datetime import datetime, timedelta, date, timezone

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connection
from django.conf import settings

from faker import Faker


# helper function
def rand_birthday():
    start = date(1940, 1, 1)
    end = date(2007, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))


def append_report(n_requested, gen_seconds, copy_seconds):
    # Append a one-line summary to reports/benchmarks.csv
    with connection.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM core_address")
        a = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM core_appuser")
        u = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM core_customerrelationship")
        r = cur.fetchone()[0]

    Path("reports").mkdir(exist_ok=True)
    out = Path("reports/copy_benchmarks.csv")
    new = not out.exists()
    total = (gen_seconds or 0) + (copy_seconds or 0)

    with open(out, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["ts", "engine", "method", "n_req", "addr",
                       "users", "rels", "gen_s", "copy_s", "total_s"])
        w.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "postgresql",
            "copy_stream",
            n_requested, a, u, r,
            round(gen_seconds, 1), round(copy_seconds, 1), round(total, 1),
        ])


class Command(BaseCommand):
    """Generate Address/AppUser/CustomerRelationship using COPY in chunks (no temp files for speed)."""

    def add_arguments(self, parser):
        parser.add_argument("--n", type=int, default=3_000_000,
                            help="Rows to generate (same for all three tables)")
        parser.add_argument("--chunk", type=int, default=100_000,
                            help="Rows per COPY call (50k–250k is fine)")

    def handle(self, *args, **opts):
        if "postgresql" not in settings.DATABASES["default"]["ENGINE"]:
            raise CommandError(
                "This command is Postgres-only. Configure DATABASES['default'] accordingly.")

        n = int(opts["n"])
        chunk = int(opts["chunk"])

        fake = Faker()
        Faker.seed(42)
        random.seed(42)

        self.stdout.write(
            f"Generating {n:,} rows via COPY (chunk={chunk:,}) ...")

        gen_seconds, copy_seconds = self.copy_stream(fake, n, chunk)
        append_report(n, gen_seconds, copy_seconds)

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. gen={round(gen_seconds, 1)}s copy={round(copy_seconds, 1)}s total={round(gen_seconds+copy_seconds, 1)}s"
            )
        )
        self.stdout.write(
            f"Report → {Path('reports/benchmarks.csv').resolve()}")

    def copy_stream(self, fake, n, chunk):
        """
        Stream rows into three in-memory CSV buffers per chunk and COPY them.
        TRUNCATE once at the start; each chunk is a small transaction = safer.
        Return (gen_seconds, copy_seconds).
        """
        t0 = time.perf_counter()
        now = datetime.now(timezone.utc)

        # start clean
        with connection.cursor() as cur, transaction.atomic():
            cur.execute(
                "TRUNCATE core_customerrelationship, core_appuser, core_address RESTART IDENTITY CASCADE;")

        address_pk = 1
        user_pk = 1
        done = 0
        copy_total = 0.0

        while done < n:
            size = min(chunk, n - done)

            address_buffer = io.StringIO()
            user_buffer = io.StringIO()
            customer_relationship_buffer = io.StringIO()
            address_writer, user_writer, customer_relationship_writer = csv.writer(address_buffer), csv.writer(
                user_buffer), csv.writer(customer_relationship_buffer)

            # generate rows for this chunk
            for _ in range(size):
                # Address
                address_writer .writerow([
                    address_pk,
                    fake.street_name(),
                    str(random.randint(1, 250)),
                    str(random.randint(1000, 99999)),
                    fake.city(),
                    fake.country(),
                ])

                # AppUser (explicit created/last_updated since COPY bypasses ORM auto fields)
                first, last = fake.first_name(), fake.last_name()
                created = now - timedelta(days=random.randint(0, 3650))
                last_upd = created + timedelta(days=random.randint(0, 3650))
                user_writer.writerow([
                    user_pk,
                    first,
                    last,
                    random.choice(["m", "f", "o"]),
                    f"cust-{random.randint(1, 5000):05d}",
                    fake.msisdn(),
                    address_pk,
                    rand_birthday().isoformat(),
                    created.isoformat(),
                    last_upd.isoformat(),
                ])

                # Customer Relationship
                customer_relationship_created = now - \
                    timedelta(days=random.randint(0, 3650))
                rel_last = customer_relationship_created + \
                    timedelta(days=random.randint(0, 3650))
                customer_relationship_writer.writerow([user_pk,
                                                       random.randint(
                                                           0, 100_000),
                                                       customer_relationship_created.isoformat(),
                                                       rel_last.isoformat()])

                address_pk += 1
                user_pk += 1

            # rewind buffers
            address_buffer.seek(0)
            user_buffer.seek(0)
            customer_relationship_buffer.seek(0)

            # COPY this chunk (small transaction so a failure doesn't lose everything)
            t_copy = time.perf_counter()
            with connection.cursor() as cur, transaction.atomic():
                cur.copy_expert("""
                    COPY core_address (id, street, street_number, city_code, city, country)
                    FROM STDIN WITH (FORMAT CSV)
                """, address_buffer)

                cur.copy_expert("""
                    COPY core_appuser
                    (id, first_name, last_name, gender, customer_id, phone_number,
                     address_id, birthday, created, last_updated)
                    FROM STDIN WITH (FORMAT CSV)
                """, user_buffer)

                cur.copy_expert("""
                    COPY core_customerrelationship (appuser_id, points, created, last_activity)
                    FROM STDIN WITH (FORMAT CSV)
                """, customer_relationship_buffer)
            copy_total += (time.perf_counter() - t_copy)

            done += size
            elapsed = time.perf_counter() - t0
            self.stdout.write(
                f"COPIED {done:,}/{n:,} (chunk={size:,})  elapsed ~{round(elapsed, 1)}s")

            # free buffers
            address_buffer.close()
            user_buffer.close()
            customer_relationship_buffer.close()

        gen_seconds = (time.perf_counter() - t0) - copy_total
        return gen_seconds, copy_total
