from rest_framework import serializers
from .models import User, UserRole

from datetime import timedelta

from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from tenants.models import Tenant, TenantStatus

# Tenants an anonymous user is allowed to join via self-registration.
# PENDING (unapproved) and EXPIRED tenants can never be joined this way.
JOINABLE_TENANT_STATUSES = [TenantStatus.TRIAL_ACTIVE, TenantStatus.ACTIVE]


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "role",
            "tenant",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        request = self.context["request"]
        requester = request.user

        tenant = attrs.get("tenant")
        role = attrs.get("role")

        if requester.role == UserRole.TENANT_ADMIN:
            if tenant and tenant.id != requester.tenant_id:
                raise serializers.ValidationError(
                    "You cannot manage users outside your tenant."
                )

            if role is not None and role != UserRole.TENANT_USER:
                raise serializers.ValidationError(
                    "Tenant Admins can only manage Tenant Users."
                )

            if self.instance and self.instance.role != UserRole.TENANT_USER:
                raise serializers.ValidationError(
                    "Tenant Admins can only manage Tenant Users."
                )

        if requester.role == UserRole.ADMIN:
            platform_roles = [
                UserRole.SUPER_ADMIN,
                UserRole.ADMIN,
                UserRole.SUPER_VIEWER,
            ]
            if role in platform_roles:
                raise serializers.ValidationError(
                    "Admins cannot assign platform-privileged roles."
                )

        if (
            role in [UserRole.TENANT_USER, UserRole.TENANT_ADMIN]
            and requester.role != UserRole.TENANT_ADMIN
            and not tenant
        ):
            raise serializers.ValidationError(
                "Tenant users and admins must belong to a tenant."
            )

        return attrs
    def create(self, validated_data):
        password = validated_data.pop("password", None)

        if not password:
            raise serializers.ValidationError(
                {"password": "Password is required when creating a user."}
            )

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()

        return instance


class TenantUserRegistrationSerializer(serializers.ModelSerializer):
    """Anonymous self-registration as TENANT_USER in an existing tenant.

    The role is fixed server-side: any client-supplied ``role`` is ignored
    (read-only) so applicants can never escalate to an administrative role.
    The tenant queryset only exposes joinable tenants, so nonexistent,
    PENDING, or EXPIRED tenant ids are rejected with a 400.
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
    )
    tenant = serializers.PrimaryKeyRelatedField(
        queryset=Tenant.objects.filter(status__in=JOINABLE_TENANT_STATUSES)
    )
    role = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "role",
            "tenant",
        ]
        read_only_fields = [
            "id",
            "role",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(role=UserRole.TENANT_USER, **validated_data)
        user.set_password(password)
        user.save()
        return user


class TenantApplicationSerializer(serializers.Serializer):
    """Anonymous application to create a new organization.

    Creates a PENDING tenant plus its TENANT_ADMIN (inactive, unusable
    password) atomically. The applicant cannot choose a role.
    """

    organization_name = serializers.CharField(max_length=255)
    admin_name = serializers.CharField(
        max_length=150,
        validators=[UnicodeUsernameValidator()],
    )
    admin_email = serializers.EmailField()

    def validate_organization_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "Organization name may not be blank."
            )
        return value

    def validate(self, attrs):
        if User.objects.filter(username=attrs["admin_name"]).exists():
            raise serializers.ValidationError(
                {"admin_name": "An account with this name already exists."}
            )
        if User.objects.filter(email=attrs["admin_email"]).exists():
            raise serializers.ValidationError(
                {"admin_email": "An account with this email already exists."}
            )
        return attrs

    def _unique_slug(self, name):
        base = slugify(name) or "organization"
        slug = base
        counter = 2
        while Tenant.objects.filter(slug=slug).exists():
            slug = f"{base}-{counter}"
            counter += 1
        return slug

    @transaction.atomic
    def create(self, validated_data):
        now = timezone.now()
        tenant = Tenant.objects.create(
            name=validated_data["organization_name"],
            slug=self._unique_slug(validated_data["organization_name"]),
            status=TenantStatus.PENDING,
            trial_started_at=now,
            trial_ends_at=now + timedelta(days=30),
        )
        user = User(
            username=validated_data["admin_name"],
            email=validated_data["admin_email"],
            role=UserRole.TENANT_ADMIN,
            tenant=tenant,
            is_active=False,
        )
        user.set_unusable_password()
        user.save()
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """Authenticated password change; clears the forced-rotation flag."""

    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(
        write_only=True, required=True, min_length=8
    )

    def validate_current_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.must_change_password = False
        user.save(update_fields=["password", "must_change_password", "updated_at"])
        return user