from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import subprocess
import sys
import os
import signal


class Command(BaseCommand):
	help = "Run both the MJPEG stream server and the Django development server"

	def add_arguments(self, parser):
		parser.add_argument('addrport', nargs='?', help='Optional port number, or ipaddr:port')
		parser.add_argument('--noreload', action='store_true', help='Tells Django to NOT use the auto-reloader.')

	def handle(self, *args, **options):
		base_dir = settings.BASE_DIR
		stream_script = os.path.join(base_dir, 'stream_mjpeg.py')
		if not os.path.exists(stream_script):
			raise SystemExit(f"stream_mjpeg.py not found at: {stream_script}")

		stream_proc = None

		def start_stream():
			nonlocal stream_proc
			self.stdout.write(self.style.SUCCESS("Starting MJPEG stream server..."))
			creationflags = 0
			preexec_fn = None
			if os.name == 'nt':
				creationflags = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
			else:
				preexec_fn = os.setsid
			stream_env = os.environ.copy()
			stream_proc = subprocess.Popen(
				[sys.executable, stream_script],
				cwd=base_dir,
				env=stream_env,
				stdout=sys.stdout,
				stderr=sys.stderr,
				creationflags=creationflags,
				preexec_fn=preexec_fn,
			)

		try:
			self.stdout.write(self.style.SUCCESS("Starting Django server..."))
			addrport = options.get('addrport')
			use_reloader = not options.get('noreload') if options.get('noreload') is not None else True

			# Only start stream from the reloader child process (RUN_MAIN == 'true'),
			# or immediately if the reloader is disabled.
			if use_reloader:
				if os.environ.get('RUN_MAIN') == 'true':
					if stream_proc is None or stream_proc.poll() is not None:
						start_stream()
			else:
				start_stream()

			if addrport:
				call_command('runserver', addrport, use_reloader=use_reloader)
			else:
				call_command('runserver', use_reloader=use_reloader)
		except KeyboardInterrupt:
			self.stdout.write("\nShutting down...")
		finally:
			# Terminate the stream process
			if stream_proc and stream_proc.poll() is None:
				try:
					if os.name == 'nt':
						stream_proc.send_signal(signal.CTRL_BREAK_EVENT)
						stream_proc.terminate()
						stream_proc.wait(timeout=5)
					else:
						os.killpg(os.getpgid(stream_proc.pid), signal.SIGTERM)
						stream_proc.wait(timeout=5)
				except Exception:
					stream_proc.kill()
					try:
						stream_proc.wait(timeout=3)
					except Exception:
						pass
			self.stdout.write(self.style.SUCCESS("All processes stopped.")) 