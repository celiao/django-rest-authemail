from django.contrib.auth import get_user_model
from rest_framework import serializers


class MyUserSerializer(serializers.ModelSerializer):
    """
    Write your own User serializer.
    """
    class Meta:
        model = get_user_model()
        fields = ('email', 'first_name', 'last_name', 'date_of_birth')


class MyUserChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'date_of_birth')
