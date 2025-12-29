# mentors/management/commands/backfill_mentor_about.py

from django.core.management.base import BaseCommand
from mentors.models import MentorProfile


class Command(BaseCommand):
    help = "Backfill mentor about (bio) with clear paragraph structure"

    def handle(self, *args, **options):
        mentors = MentorProfile.objects.all()
        updated = 0

        for mentor in mentors:
            bio_parts = []

            # === HEADLINE ===
            if mentor.headline:
                bio_parts.append(f"### Overview\n{mentor.headline.strip()}")

            # === POSITION ===
            if mentor.current_position:
                bio_parts.append(
                    f"### Current Role\nCurrently working as {mentor.current_position.strip()}."
                )

            # === PRIMARY FOCUS ===
            if mentor.primary_focus:
                bio_parts.append(
                    "### Primary Focus\n"
                    f"{mentor.primary_focus.strip()}."
                )

            # === SESSION FOCUS ===
            if mentor.session_focus:
                bio_parts.append(
                    "### Session Focus\n"
                    f"{mentor.session_focus.strip()}."
                )

            # === INDUSTRY ===
            if mentor.industry:
                bio_parts.append(
                    "### Industry Background\n"
                    f"{mentor.industry.strip()}."
                )

            # === EXPERTISE ===
            if mentor.specializations:
                bio_parts.append(
                    "### Areas of Expertise\n"
                    + ", ".join(mentor.specializations)
                )

            if not bio_parts:
                continue

            mentor.bio = "\n\n".join(bio_parts)
            mentor.save(update_fields=["bio"])
            updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"Backfilled about for {updated} mentors.")
        )
