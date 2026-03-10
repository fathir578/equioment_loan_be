# ============================================================
#  core/middleware.py — Custom middleware
# ============================================================


class ActivityLogMiddleware:
    """
    Middleware untuk auto-log aksi penting.
    Jalan di setiap request — tapi kita filter
    hanya method yang mengubah data (POST, PUT, PATCH, DELETE).

    Kenapa middleware bukan di tiap view?
    → DRY (Don't Repeat Yourself) — satu tempat untuk semua logging.
      Tidak perlu ingat nulis log di setiap endpoint.
    """

    # Endpoint yang tidak perlu di-log (terlalu noise)
    SKIP_PATHS = [
        '/api/docs/',
        '/api/schema/',
        '/admin/',
        '/static/',
        '/media/',
    ]

    # Hanya log method yang mengubah data
    LOG_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Jalankan view dulu, baru log setelahnya
        response = self.get_response(request)

        # Filter: hanya log jika method relevan dan response sukses
        should_log = (
            request.method in self.LOG_METHODS
            and response.status_code < 400
            and not any(request.path.startswith(p) for p in self.SKIP_PATHS)
            and hasattr(request, 'user')
            and request.user.is_authenticated
        )

        if should_log:
            self._write_log(request, response)

        return response

    def _write_log(self, request, response):
        """
        Tulis log secara async-safe menggunakan import lazy
        untuk menghindari circular import.
        """
        try:
            # Import di sini (bukan di atas) untuk hindari circular import
            from apps.activity_logs.models import ActivityLog

            # Buat deskripsi yang informatif
            action = f"{request.method} {request.path}"
            description = (
                f"Status: {response.status_code} | "
                f"User: {request.user.username} | "
                f"IP: {self._get_client_ip(request)}"
            )

            ActivityLog.objects.create(
                user        = request.user,
                action      = action,
                description = description,
                ip_address  = self._get_client_ip(request),
            )
        except Exception:
            # Jangan sampai error logging menghentikan request utama
            pass

    @staticmethod
    def _get_client_ip(request):
        """
        Ambil IP asli client.
        X-Forwarded-For dipakai kalau ada proxy/load balancer di depan.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')
