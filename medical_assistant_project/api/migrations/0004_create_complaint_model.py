# Generated manually

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_alter_document_document_type'),  # Update this to match your latest migration
    ]

    operations = [
        migrations.CreateModel(
            name='Complaint',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('reference_number', models.CharField(blank=True, max_length=100, null=True)),
                ('practice', models.CharField(blank=True, max_length=255, null=True)),
                ('form_date', models.DateField(blank=True, null=True)),
                ('reporter_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='Person Completing the Report')),
                ('group', models.CharField(blank=True, max_length=255, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('patient_name', models.CharField(blank=True, max_length=255, null=True)),
                ('patient_nhi', models.CharField(blank=True, max_length=100, null=True, verbose_name='Patient NHI')),
                ('patient_dob', models.DateField(blank=True, null=True, verbose_name='Patient DOB')),
                ('patient_email', models.EmailField(blank=True, max_length=254, null=True)),
                ('patient_phone', models.CharField(blank=True, max_length=50, null=True, verbose_name='Patient Phone Number')),
                ('is_acknowledged', models.BooleanField(default=False, verbose_name="Has the patient's complaint been acknowledged?")),
                ('received_date', models.DateField(blank=True, null=True, verbose_name='Date Complaint was Received')),
                ('complaint_method', models.CharField(blank=True, max_length=100, null=True)),
                ('complaint_severity', models.CharField(blank=True, max_length=100, null=True)),
                ('complaint_owner', models.CharField(blank=True, max_length=255, null=True)),
                ('complaint_details', models.TextField(blank=True, null=True)),
                ('action_taken', models.TextField(blank=True, null=True, verbose_name='Action Taken at the Time of Complaint and By Whom')),
                ('is_notified_external', models.BooleanField(default=False, verbose_name='Was the complaint notified to an external organisation?')),
                ('other_comments', models.TextField(blank=True, null=True, verbose_name='Any Other Comments')),
                ('file_upload_path', models.CharField(blank=True, max_length=1024, null=True)),
                ('request_review_by', models.CharField(blank=True, max_length=255, null=True)),
                ('complaint_reason', models.TextField(blank=True, null=True, verbose_name='Reason for the Patient Complaint')),
                ('is_resolved', models.BooleanField(default=False, verbose_name='Was the Complaint Successfully Resolved?')),
                ('identified_issues', models.TextField(blank=True, null=True, verbose_name='Identified Issues as a Result of the Complaint')),
                ('staff_skill_issues', models.TextField(blank=True, null=True, verbose_name='Issues Related to Staff Skill or Knowledge')),
                ('policy_impact', models.TextField(blank=True, null=True, verbose_name='Did Practice Policies/Protocols Help or Hinder?')),
                ('is_disclosure_required', models.BooleanField(default=False, verbose_name='Is Open Disclosure Required?')),
                ('is_followup_required', models.BooleanField(default=False, verbose_name='Is Follow-Up Action Required?')),
                ('is_event_analysis_required', models.BooleanField(default=False, verbose_name='Is Formal Significant Event Analysis Required?')),
                ('is_training_required', models.BooleanField(default=False, verbose_name='Is Staff Training Required?')),
                ('is_visible_to_users', models.BooleanField(default=True, verbose_name='Make Complaint Management Visible to Users')),
                ('disable_editing', models.BooleanField(default=False, verbose_name='Disable Editing by Users')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
