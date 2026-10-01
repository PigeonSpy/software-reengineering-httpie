import errno

from .argument_processor import HTTPieArgumentProcessor

class HTTPieEnvironmentProcessor(HTTPieArgumentProcessor):
    """Handles environment and stream setup based on parsed arguments."""

    def _setup_standard_streams(self):
        """
        Refactored stream setup: Separates concerns
        """
        self.args.output_file_specified = bool(self.args.output_file)

        if self.args.download:
            self._setup_download_mode()
        elif self.args.output_file:
            self._setup_output_file_mode()
        if self.args.quiet:
            self._setup_quiet_mode()
  
    def _setup_download_mode(self):
        if not self.args.output_file and not self.env.stdout_isatty:
            self.args.output_file = self.env.stdout

        self.env.stdout = self.env.stderr
        self.env.stdout_isatty = self.env.stderr_isatty

    def _setup_output_file_mode(self):
        try:
            self.args.output_file.seek(0)
            self.args.output_file.truncate()
        except (OSError, IOError) as e:
            if getattr(e, 'errno', None) != errno.EINVAL:
                raise
        
        self.env.stdout = self.args.output_file
        self.env.stdout_isatty = False

    def _setup_quiet_mode(self):
        self.env.quiet = True
        self.env.stderr = self.env.devnull

        if not (self.args.output_file_specified and not self.args.download):
            self.env.stdout = self.env.devnull

        self.env.apply_warnings_filter()