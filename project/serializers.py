from rest_framework import serializers
from .models import Expenditure, Commitment, SeedGrant, TDGGrant, FundRequest, Project,BillInward,Faculty, Payment, Receipt, TDSSection,TDSRate, ProjectSanctionDistribution, ReceiptHead, Payee
import re

# ✅ Base Serializer with Grant Support
class GrantRelatedSerializer(serializers.ModelSerializer):
    """Base serializer for models with seed_grant/tdg_grant FK"""
    grant_no_display = serializers.SerializerMethodField()
    seed_grant_short = serializers.CharField(source='seed_grant.short_no', read_only=True, allow_null=True)
    tdg_grant_short = serializers.CharField(source='tdg_grant.short_no', read_only=True, allow_null=True)
    
    def get_grant_no_display(self, obj):
        """Return full grant number for display"""
        if obj.seed_grant:
            return obj.seed_grant.grant_no
        elif obj.tdg_grant:
            return obj.tdg_grant.grant_no
        return ""
    
    def validate(self, data):
        seed = self.initial_data.get('seed_grant')
        tdg = self.initial_data.get('tdg_grant')

        if not seed and not tdg:
            raise serializers.ValidationError(
                "Either seed_grant or tdg_grant is required"
            )
        
        if seed and tdg:
            raise serializers.ValidationError(
                "Select only one grant type (Seed or TDG)"

            )
        return data 




       
    
    def create(self, validated_data):
    
        if validated_data.get('seed_grant'):
            validated_data['tdg_grant'] = None

        if validated_data.get('tdg_grant'):
            validated_data['seed_grant'] = None

        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Handle grant updates properly"""
        if 'seed_grant' in validated_data and validated_data['seed_grant']:
            instance.tdg_grant = None
        if 'tdg_grant' in validated_data and validated_data['tdg_grant']:
            instance.seed_grant = None
        
        return super().update(instance, validated_data)


# ✅ Expenditure Serializer
class    ExpenditureSerializer(GrantRelatedSerializer):
    seed_grant = serializers.PrimaryKeyRelatedField(queryset=SeedGrant.objects.all(), allow_null=True, required=False)

    tdg_grant = serializers.PrimaryKeyRelatedField(queryset=TDGGrant.objects.all(), allow_null=True, required=False)

     
    class Meta:
        model = Expenditure
        fields = [
            'id', 'date', 'head', 'particulars', 'amount', 'remarks',
            'seed_grant', 'tdg_grant',
            'grant_no_display', 'seed_grant_short', 'tdg_grant_short'  ]

   


    def validate(self, data):
        project = data.get("seed_grant") or data.get("tdg_grant")
        date_val = data.get("date")

        if project and date_val:
            effective_end = project.get_effective_end_date()

            if date_val > effective_end:
                raise serializers.ValidationError(
                    "This project is expired. Please contact admin to extend the project."
                )

            if project.project_status != "ONGOING":
                raise serializers.ValidationError(
                    "This project is not active. Please contact admin."
                )

        return data
    
    

        


# ✅ Commitment Serializer
class CommitmentSerializer(GrantRelatedSerializer):
    seed_grant = serializers.PrimaryKeyRelatedField(queryset=SeedGrant.objects.all(), allow_null=True, required=False)
    tdg_grant = serializers.PrimaryKeyRelatedField(queryset=TDGGrant.objects.all(), allow_null=True, required=False )
    class Meta:
        model = Commitment
        fields = [
            'id', 'date', 'head', 'particulars', 'gross_amount', 'remarks',
            'seed_grant', 'tdg_grant',
            'grant_no_display', 'seed_grant_short', 'tdg_grant_short'
        ]
    def validate(self, data):
        project = data.get("seed_grant") or data.get("tdg_grant")
        date_val = data.get("date")

        if project and date_val:
            effective_end = project.get_effective_end_date()

            if date_val > effective_end:
                raise serializers.ValidationError(
                    "This project is expired. Please contact admin to extend the project."
                )

            if project.project_status != "ONGOING":
                raise serializers.ValidationError(
                    "This project is not active. Please contact admin."
                )

        return data
    
    

 


# ✅ SeedGrant Serializer (Simple - no FK relations)
class SeedGrantSerializer(serializers.ModelSerializer):
    
    pi_name = serializers.CharField(source="faculty.pi_name", read_only=True)
    faculty_department = serializers.CharField(source="faculty.department", read_only=True)
    final_end_date = serializers.SerializerMethodField()
    extension_approved_by_name = serializers.SerializerMethodField()

    
    class Meta:
        model = SeedGrant
        fields = "__all__"
        read_only_fields = ["project_status"]
    def validate(self, attrs):
        is_extended = attrs.get(
            "is_extended",
            getattr(self.instance, "is_extended", False)

        )

        if self.instance and is_extended is False:
            return attrs

        extended_end_date = attrs.get(
            "extended_end_date",
            getattr(self.instance, "extended_end_date", None)

        )

        end_date = attrs.get(
            "end_date",
            getattr(self.instance, "end_date", None)
        )

        if is_extended and not extended_end_date:
            raise serializers.ValidationError({
                "extended_end_date": "Extended end date is required when project is marked as extended."
            })
        
        if not is_extended and extended_end_date:
            raise serializers.ValidationError({
                "extended_end_date": "Extended end date must be empty unless project is extended. "
            })
        if(
            is_extended
            and extended_end_date
            and end_date
            and extended_end_date < end_date

        ):
            raise serializers.ValidationError({
                "extended_end_date": "Extended end date cannot be earlier than project end date. "
            })
        return attrs
    
    def get_extension_approved_by_name(self, obj):
        if obj.extension_approved_by:
            return (
                obj.extension_approved_by.get_full_name()
                or obj.extension_approved_by.username
            )
        return None

    def _protect_system_fields(self, validated_data):
        validated_data.pop("project_status", None)
        validated_data.pop("extension_approved_by", None)
        return validated_data
    
    def create(self,validated_data):
        user = self.context["request"].user

        validated_data = self._protect_system_fields(self, validated_data)


        if not user.is_superuser:
            validated_data.pop("is_extended", None)
            validated_data.pop("extended_end_date", None)
            validated_data.pop("extension_reason", None)
            validated_data.pop("extension_approved_by", None)
        else:
            if validated_data.get("is_extended") is True:
                validated_data["extension_approved_by"] = user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        user = self.context["request"].user

        validated_data = self._protect_system_fields(validated_data)

        is_extended = validated_data.get(
            "is_extended",
            instance.is_extended
        )

        if user.is_superuser:
            if is_extended:
                validated_data["extension_approved_by"] = user
                     
                
            
            else:
                validated_data["extended_end_date"] = None
                validated_data["extension_reason"] = None
                validated_data["extension_approved_by"] = None

        else:
            validated_data.pop("is_extended", None)
            validated_data.pop("extended_end_date", None)
            validated_data.pop("extension_reason", None)
            validated_data.pop("extension_approved_by", None)

        return super().update(instance, validated_data)

           

        
    def get_final_end_date(self, obj):
        return obj.get_effective_end_date()



# ✅ TDGGrant Serializer (Simple - no FK relations)
class TDGGrantSerializer(serializers.ModelSerializer):
    
    pi_name = serializers.CharField(source="faculty.pi_name", read_only=True)
    faculty_department = serializers.CharField(source="faculty.department", read_only=True)
    final_end_date = serializers.SerializerMethodField()
    extension_approved_by_name = serializers.SerializerMethodField()
    
    
    class Meta:
        model = TDGGrant
        fields = '__all__'
        read_only_fields = ['short_no']

    def validate(self, attrs):
        is_extended = attrs.get("is_extended",
                                getattr(self.instance, "is_extended", False)
        )

        if self.instance and is_extended is False:
            return attrs

        extended_end_date = attrs.get(
            "extended_end_date",
            getattr(self.instance, "extended_end_date", None)
        )

        end_date = attrs.get(
            "end_date",
            getattr(self.instance, "end_date", None)
        )

        if is_extended and not extended_end_date:
            raise serializers.ValidationError({
                "extended_end_date": "Extended end date is required when project is marked as extended."
            })
        
        if not is_extended and extended_end_date:
            raise serializers.ValidationError({
                "extended_end_date": "Extended end date must be empty unless project is extended. "
            })
        
        if(
            is_extended
            and extended_end_date
            and end_date
            and extended_end_date < end_date
        ):
            raise serializers.ValidationError({
                "extended_end_date": "Extended end date cannot be earlier than project end date."
            })
        return attrs
    
    def get_extension_approved_by_name(self, obj):
        if obj.extension_approved_by:
            return (
                obj.extension_approved_by.get_full_name()
                or obj.extension_approved_by.username

            )
        return None

    def _protect_system_fields(self, validated_data):
        validated_data.pop("project_status", None)
        validated_data.pop("extension_approved_by", None)
        return validated_data

    def create(self,validated_data):
        user = self.context["request"].user

        if not user.is_superuser:
            validated_data.pop("is_extended", None)
            validated_data.pop("extended_end_date", None)
            validated_data.pop("extension_reason", None)
            validated_data.pop("extension_approved_by", None)
        else:
            if validated_data.get("is_extended") is True:
                validated_data["extension_approved_by"] = user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        user = self.context["request"].user

        validated_data = self._protect_system_fields(validated_data)
        is_extended = validated_data.get(
            "is_extended",
            instance.is_extended
        )

        if user.is_superuser:
            if is_extended:
                validated_data["extension_approved_by"] = user

            else:
                validated_data["extended_end_date"] = None
                validated_data["extension_reason"] = None
                validated_data["extension_approved_by"] = None
        else:
            validated_data.pop("is_extended", None)
            validated_data.pop("extended_end_date", None)
            validated_data.pop("extension_reason", None)
            validated_data.pop("extension_approved_by", None)
        return super().update(instance, validated_data)

    def get_final_end_date(self,obj):
        return obj.get_effective_end_date()

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'

    def validate(self, attrs):
        """
        Enforce project extension business rules at API level 
        """
        #Existing values (for update)
        is_extended = attrs.get(
            "is_extended",
            getattr(self.instance, "is_extended", False)
        )

        extended_end_date = attrs.get(
            "extended_end_date",
            getattr(self.instance, "extended_end_date", None)
        )

        project_end_date = attrs.get(
            "project_end_date",
            getattr(self.instance, "project_end_date", None)
        )

        if is_extended and not extended_end_date:
            raise serializers.ValidationError({
                "extended_end_date": "Extended end date is required when project is marked as extended. "
            })
        
        if not is_extended and extended_end_date:
            raise serializers.ValidationError({
                "extended_end_date": "Extended end date must be empty unless project is extended. "
            })
        
        if(
            is_extended
            and extended_end_date
            and project_end_date
            and extended_end_date < project_end_date
        ):
            raise serializers.ValidationError({
                "extended_end_date": "Extended end date cannot be earlier than project end date."
            })
        return attrs
    def _protect_system_fields(self, validated_data):
        validated_data.pop("project_status", None)
        validated_data.pop("extension_approved_by", None)
        return validated_data
    
    def create(self, validated_data):
        user = self.context["request"].user

        validated_data = self._protect_system_fields(validated_data)

        if not user.is_superuser:
            validated_data.pop("is_extended", None)
            validated_data.pop("extended_end_date", None)
            validated_data.pop("extension_reason", None)
            validated_data.pop("extension_approved_by", None)
        else:
            if validated_data.get("is_extended") is True:
                validated_data["extension_approved_by"] = user

        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        validated_data.pop("project_status", None)
        user = self.context["request"].user

        validated_data = self._protect_system_fields(validated_data)

        if not user.is_superuser:
            validated_data.pop("is_extended", None)
            validated_data.pop("extended_end_date", None)
            validated_data.pop("extended_reason", None)
            validated_data.pop("extension_approved_by", None)
        else:
            if validated_data.get("is_extended") is True:
                instance.extension_approved_by = user

        return super().update(instance, validated_data)



class FundRequestSerializer(serializers.ModelSerializer):
    faculty_username = serializers.CharField(source='faculty.username', read_only=True)
    project_type = serializers.SerializerMethodField()

    class Meta:
        model = FundRequest
        fields = [
            'id', 
            'faculty', 
            'faculty_username',
            'pi_name', 
            'faculty_id',
            'project', 
            'seed_grant', 
            'tdg_grant',
            'project_type',
            'project_no', 
            'project_title', 
            'short_no',
            'head', 
            'particulars', 
            'amount',
            'status', 
            'remarks_by_src',
            'request_date', 
            'updated_date'
        ]

        read_only_fields = [
            'faculty', 
            'pi_name', 
            'faculty_id',
            'project', 
            'seed_grant', 
            'tdg_grant',
            'project_no', 
            'project_title', 
            'short_no',
            'head', 
            'particulars', 
            'amount',
            'request_date', 
            'updated_date'
        ]

    def get_project_type(self, obj):
            """Determine project type for display"""
            if obj.project:
               return 'Project'
            elif obj.seed_grant:
               return 'Seed Grant'
            elif obj.tdg_grant:
               return 'TDG Grant'
            return 'N/A'

    def validate_status(self, value):
            """Validate status choices"""
            valid_statuses = ['pending', 'approved', 'rejected']
            if value not in valid_statuses:
                raise serializers.ValidationError(f"Status must be one of: {', '.join(valid_statuses)}")
            return value
    
class BillInwardSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True) 
    faculty = serializers.SlugRelatedField(slug_field="faculty_id", queryset=Faculty.objects.all())
    tds_section = serializers.PrimaryKeyRelatedField(queryset=TDSSection.objects.all(), allow_null=True, required=False)
    tds_rate = serializers.PrimaryKeyRelatedField(queryset=TDSRate.objects.all(), allow_null=True, required=False)
    pi_name = serializers.CharField(source="faculty.pi_name", read_only=True)
    # Optional: Display fields for better UI (read-only)
    faculty_id_display = serializers.CharField(source='faculty.faculty_id',  read_only=True, required=False)
    
    
    assigned_to_name = serializers.SerializerMethodField(read_only=True)
    
    status_display = serializers.CharField(
        source='get_bill_status_display',
        read_only=True
    )

    bill_pdf_url = serializers.SerializerMethodField()
    can_upload_pdf = serializers.SerializerMethodField()
    
    class Meta:
        model = BillInward
        fields = '__all__'
    
    def get_assigned_to_name(self, obj):
        """Show assigned admin member name"""
        if obj.whom_to:
            return obj.whom_to.get_full_name() or obj.whom_to.username
        return None
    
    def get_bill_pdf_url(self, obj):
        if obj.bill_pdf:
            request = self.context.get('request') 
            if request:
                return request.build_absolute_uri(obj.bill_pdf.url)
        return None
    
    def get_can_upload_pdf(self, obj):
        request = self.context["request"]
        user = request.user

        if user.is_superuser:
            return True
        
        if user.groups.filter(name="billinward").exists():
            return True
        return False
    
class PaymentSerializer(serializers.ModelSerializer):
    pi_name = serializers.CharField(source="faculty.pi_name", read_only=True)
    tds_section = serializers.IntegerField(source="tds_section.id", read_only=False,allow_null=True)
    tds_rate = serializers.IntegerField(source="tds_rate.id", read_only=False, allow_null=True)
    
    
    def validate(self, data):
        project = data.get("project")
        date_val = data.get("date")

        if project and date_val:
            final_end = project.final_end_date

            if date_val > final_end:
                raise serializers.ValidationError(
                    "This project is expired. Please contact admin to extend."
            )

            if project.project_status == "CLOSED":
                raise serializers.ValidationError(
                      "This project is closed. Please contact admin."
                )
            return data


    class Meta:
        model = Payment
        fields = '__all__'            

class ReceiptSerializer(serializers.ModelSerializer):

    def validate(self, data):
        project = data.get("project")
        date_val = data.get("receipt_date")

        if project and date_val:
            effective_end = project.get_effective_end_date()

            if date_val > effective_end:
                raise serializers.ValidationError(
                    "This project is expired. Please contact admin to extend."
            )

            if project.project_status == "CLOSED":
                raise serializers.ValidationError(
                      "This project is closed. Please contact admin."
                )
            return data
    class Meta:
        model = Receipt
        fields = '__all__'

        


class ProjectSanctionDistributionSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all()
    )

    faculty = serializers.SlugRelatedField(
        slug_field="faculty_id",
        queryset=Faculty.objects.all(),
        allow_null=True,
        required=False
    )

    head = serializers.PrimaryKeyRelatedField(
        queryset=ReceiptHead.objects.all()
    )

    project_no = serializers.CharField(read_only=True)
    project_title = serializers.CharField(read_only=True)
    pi_name = serializers.CharField(read_only=True)
    department = serializers.CharField(read_only=True)

    class Meta:
        model = ProjectSanctionDistribution
        fields = [
            "id",
            "project",
            "faculty",
            "financial_year",
            "head",
            "sanctioned_amount",
            "project_no",
            "project_title",
            "pi_name",
            "department",
            "remarks",
        ]

        read_only_fields = [
            "project_no",
            "project_title",
            "pi_name",
            "department",
        ]

    def validate_financial_year(self, value):
        if not re.match(r'^\d{4}-\d{2}$', value):
            raise serializers.ValidationError(
                "Financial year must be in format YYYY-YY (e.g. 2024-25)"
            )
        
        
        return value

    def validate_sanctioned_amount(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Sanctioned amount cannot be negative."
            )
        return value
    
    def validate(self, data):
        project = data.get("project")
        financial_year = data.get("financial_year")
        head = data.get("head")

        qs = ProjectSanctionDistribution.objects.filter(
            project=project,
            financial_year=financial_year,
            head=head,
        )

        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError(
                "Sanction distribution already exists for this project, year and head."
            )
        return data 
    
class PayeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payee
        fields = "__all__"