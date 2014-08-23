from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers


class MyUserSerializer(serializers.ModelSerializer):
    """
    Write your own User serializer.
    """
    class Meta:
        model = get_user_model()
        fields = ('email', 'first_name', 'last_name', 'date_of_birth')
