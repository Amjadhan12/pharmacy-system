from rest_framework import serializers

from .models import JournalEntry, JournalLine, LedgerAccount


class LedgerAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerAccount
        fields = [
            "id", "account_code", "name", "account_type", "currency", "pharmacy",
            "parent", "position_order", "is_active", "description",
            "increase_side", "decrease_side", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {"parent": {"required": False}}


class JournalLineSerializer(serializers.ModelSerializer):
    account = serializers.PrimaryKeyRelatedField(
        queryset=LedgerAccount.objects.none(), write_only=True
    )

    class Meta:
        model = JournalLine
        fields = ["id", "account", "debit", "credit", "balance"]
        read_only_fields = ["id", "balance"]

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        if request is not None and self.instance is None:
            default_ph = request.user.pharmacies.first() if request.user.is_authenticated else None
            fields["account"].queryset = (
                LedgerAccount.objects.none()
                if default_ph is None
                else default_ph.accounts.filter(is_active=True)
            )
        return fields


class JournalEntrySerializer(serializers.ModelSerializer):
    lines = JournalLineSerializer(many=True, read_only=True)

    class Meta:
        model = JournalEntry
        fields = [
            "id", "journal_code", "entry_date", "reference", "description",
            "is_open", "debit_total", "credit_total", "is_balanced", "lines",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "journal_code", "debit_total", "credit_total", "is_balanced", "created_at", "updated_at"]
