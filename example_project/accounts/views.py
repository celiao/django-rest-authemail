from django.utils.translation import gettext as _

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import MyUserSerializer, MyUserChangeSerializer


class MyUserMe(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MyUserSerializer

    def get(self, request, format=None):
        return Response(self.serializer_class(request.user).data)


class MyUserMeChange(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MyUserChangeSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            user = request.user

            if 'first_name' in serializer.data:
                user.first_name = serializer.data['first_name']
            if 'last_name' in serializer.data:
                user.last_name = serializer.data['last_name']
            if 'date_of_birth' in serializer.data:
                user.date_of_birth = serializer.data['date_of_birth']

            user.save()

            content = {'success': _('User information changed.')}
            return Response(content, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
