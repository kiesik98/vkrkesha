from django.shortcuts import redirect


class AnonymousRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_staff:
            return redirect('admin:index')
        return super().dispatch(request, *args, **kwargs)

