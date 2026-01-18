# management/commands/ask_claude.py
from django.core.management.base import BaseCommand
import anthropic
import os


class Command(BaseCommand):
    help = 'Demande de l\'aide à Claude IA'

    def add_arguments(self, parser):
        parser.add_argument('question', type=str, help='Votre question')

    def handle(self, *args, **options):
        client = anthropic.Anthropic(api_key=os.getenv('CLAUDE_API_KEY'))

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": options['question']}
            ]
        )

        self.stdout.write(self.style.SUCCESS(message.content[0].text))