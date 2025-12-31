from rest_framework import generics, permissions

from profiles.models import Profile
from profiles.serializers import ProfileSerializer


class MeProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return Profile.objects.select_related("user").get(user=self.request.user)
