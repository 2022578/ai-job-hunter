"""
Applications Page - Application management with HR contact tracking
"""

import streamlit as st
import logging
import pandas as pd
from typing import List, Optional, Dict, Any
from datetime import datetime
from io import BytesIO
from database.repositories.application_repository import ApplicationRepository
from database.repositories.hr_contact_repository import HRContactRepository
from database.repositories.job_repository import JobRepository
from models.application import Application
from models.hr_contact import HRContact

logger = logging.getLogger(__name__)


def initialize_session_state():
    """Initialize session state variables for applications page"""
    if 'selected_application_id' not in st.session_state:
        st.session_state.selected_application_id = None
    
    if 'show_hr_form' not in st.session_state:
        st.session_state.show_hr_form = False
    
    if 'show_hr_directory' not in st.session_state:
        st.session_state.show_hr_directory = False
    
    if 'hr_search_query' not in st.session_state:
        st.session_state.hr_search_query = ""


def render_statistics(app_repo: ApplicationRepository):
    """
    Render application statistics
    
    Args:
        app_repo: Application repository instance
    """
    try:
        stats = app_repo.get_statistics(st.session_state.user_id)
        
        st.subheader("📊 Application Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Applications", stats.get('total', 0))
        
        with col2:
            total_applied = sum([
                stats.get('by_status', {}).get('applied', 0),
                stats.get('by_status', {}).get('interview', 0),
                stats.get('by_status', {}).get('offered', 0),
                stats.get('by_status', {}).get('rejected', 0)
            ])
            st.metric("Actually Applied", total_applied)
        
        with col3:
            interview_rate = stats.get('interview_rate', 0)
            st.metric("Interview Rate", f"{interview_rate:.1f}%")
        
        with col4:
            offer_rate = stats.get('offer_rate', 0)
            st.metric("Offer Rate", f"{offer_rate:.1f}%")
        
        # Status breakdown
        st.markdown("---")
        st.markdown("**Status Breakdown:**")
        
        by_status = stats.get('by_status', {})
        status_cols = st.columns(len(Application.VALID_STATUSES))
        
        status_labels = {
            'saved': '💾 Saved',
            'applied': '📝 Applied',
            'interview': '💼 Interview',
            'offered': '🎉 Offered',
            'rejected': '❌ Rejected',
            'not_interested': '🚫 Not Interested'
        }
        
        for idx, status in enumerate(Application.VALID_STATUSES):
            with status_cols[idx]:
                count = by_status.get(status, 0)
                st.metric(status_labels.get(status, status), count)
        
    except Exception as e:
        logger.error(f"Failed to render statistics: {e}")
        st.error("Failed to load statistics")


def get_application_display_data(applications: List[Application], job_repo: JobRepository, hr_repo: HRContactRepository) -> List[Dict[str, Any]]:
    """
    Get display data for applications with job and HR contact info
    
    Args:
        applications: List of applications
        job_repo: Job repository instance
        hr_repo: HR contact repository instance
        
    Returns:
        List of dictionaries with display data
    """
    display_data = []
    
    for app in applications:
        # Get job details
        job = job_repo.find_by_id(app.job_id)
        
        # Get HR contact if exists
        hr_contact_name = "N/A"
        if app.hr_contact_id:
            hr_contact = hr_repo.find_by_id(app.hr_contact_id)
            if hr_contact:
                hr_contact_name = hr_contact.name
        
        display_data.append({
            'application_id': app.id,
            'job_title': job.title if job else "Unknown",
            'company': job.company if job else "Unknown",
            'status': app.status,
            'applied_date': app.applied_date.strftime('%Y-%m-%d') if app.applied_date else "N/A",
            'interview_date': app.interview_date.strftime('%Y-%m-%d') if app.interview_date else "N/A",
            'hr_contact': hr_contact_name,
            'notes': app.notes[:50] + "..." if len(app.notes) > 50 else app.notes
        })
    
    return display_data


def render_applications_table(app_repo: ApplicationRepository, job_repo: JobRepository, hr_repo: HRContactRepository):
    """
    Render applications table with status update functionality
    
    Args:
        app_repo: Application repository instance
        job_repo: Job repository instance
        hr_repo: HR contact repository instance
    """
    try:
        # Get all applications
        applications = app_repo.find_by_user(st.session_state.user_id)
        
        if not applications:
            st.info("No applications yet. Start by searching for jobs and saving them!")
            return
        
        st.subheader(f"📋 Your Applications ({len(applications)})")
        
        # Filter by status
        col1, col2 = st.columns([2, 1])
        
        with col1:
            status_filter = st.selectbox(
                "Filter by Status",
                options=["All"] + Application.VALID_STATUSES,
                index=0
            )
        
        with col2:
            sort_by = st.selectbox(
                "Sort By",
                options=["Recent First", "Oldest First", "Company", "Status"],
                index=0
            )
        
        # Apply filters
        filtered_apps = applications
        if status_filter != "All":
            filtered_apps = [app for app in applications if app.status == status_filter]
        
        # Apply sorting
        if sort_by == "Recent First":
            filtered_apps = sorted(filtered_apps, key=lambda x: x.created_at, reverse=True)
        elif sort_by == "Oldest First":
            filtered_apps = sorted(filtered_apps, key=lambda x: x.created_at)
        elif sort_by == "Company":
            # Need to get job details for sorting
            filtered_apps = sorted(filtered_apps, key=lambda x: job_repo.find_by_id(x.job_id).company if job_repo.find_by_id(x.job_id) else "")
        elif sort_by == "Status":
            filtered_apps = sorted(filtered_apps, key=lambda x: x.status)
        
        if not filtered_apps:
            st.info(f"No applications with status: {status_filter}")
            return
        
        # Display applications
        for app in filtered_apps:
            render_application_card(app, app_repo, job_repo, hr_repo)
        
    except Exception as e:
        logger.error(f"Failed to render applications table: {e}", exc_info=True)
        st.error(f"Failed to load applications: {str(e)}")


def render_application_card(app: Application, app_repo: ApplicationRepository, job_repo: JobRepository, hr_repo: HRContactRepository):
    """
    Render a single application card
    
    Args:
        app: Application instance
        app_repo: Application repository instance
        job_repo: Job repository instance
        hr_repo: HR contact repository instance
    """
    # Get job details
    job = job_repo.find_by_id(app.job_id)
    
    if not job:
        st.warning(f"Job not found for application {app.id}")
        return
    
    with st.container():
        # Card header
        col1, col2, col3 = st.columns([3, 2, 1])
        
        with col1:
            st.markdown(f"### {job.title}")
            st.markdown(f"**{job.company}** • {job.location}")
        
        with col2:
            # Status dropdown
            current_status_idx = Application.VALID_STATUSES.index(app.status)
            new_status = st.selectbox(
                "Status",
                options=Application.VALID_STATUSES,
                index=current_status_idx,
                key=f"status_{app.id}",
                label_visibility="collapsed"
            )
            
            if new_status != app.status:
                update_application_status(app.id, new_status, app_repo)
        
        with col3:
            # Status badge
            status_colors = {
                'saved': 'blue',
                'applied': 'green',
                'interview': 'orange',
                'offered': 'purple',
                'rejected': 'red',
                'not_interested': 'gray'
            }
            color = status_colors.get(app.status, 'gray')
            st.markdown(f"<div style='text-align: center; background-color: {color}; color: white; padding: 5px; border-radius: 5px; font-weight: bold;'>{app.status.upper()}</div>", unsafe_allow_html=True)
        
        # Application details
        col1, col2, col3 = st.columns(3)
        
        with col1:
            applied_text = app.applied_date.strftime('%Y-%m-%d') if app.applied_date else "Not applied yet"
            st.markdown(f"📅 **Applied:** {applied_text}")
        
        with col2:
            interview_text = app.interview_date.strftime('%Y-%m-%d') if app.interview_date else "Not scheduled"
            st.markdown(f"💼 **Interview:** {interview_text}")
        
        with col3:
            # HR contact
            hr_contact_text = "No contact"
            if app.hr_contact_id:
                hr_contact = hr_repo.find_by_id(app.hr_contact_id)
                if hr_contact:
                    hr_contact_text = hr_contact.name
            st.markdown(f"👤 **HR Contact:** {hr_contact_text}")
        
        # Notes
        if app.notes:
            with st.expander("📝 Notes"):
                st.markdown(app.notes)
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("👁️ View Job", key=f"view_job_{app.id}", use_container_width=True):
                view_job_details(job.id)
        
        with col2:
            if st.button("👤 Manage HR", key=f"manage_hr_{app.id}", use_container_width=True):
                st.session_state.selected_application_id = app.id
                st.session_state.show_hr_form = True
                st.rerun()
        
        with col3:
            if st.button("✏️ Edit Notes", key=f"edit_notes_{app.id}", use_container_width=True):
                edit_application_notes(app, app_repo)
        
        with col4:
            if st.button("🗑️ Delete", key=f"delete_{app.id}", use_container_width=True):
                delete_application(app.id, app_repo)
        
        st.markdown("---")


def update_application_status(application_id: str, new_status: str, app_repo: ApplicationRepository):
    """
    Update application status
    
    Args:
        application_id: Application ID to update
        new_status: New status value
        app_repo: Application repository instance
    """
    try:
        if app_repo.update_status(application_id, new_status):
            st.success(f"✅ Status updated to: {new_status}")
            st.rerun()
        else:
            st.error("Failed to update status")
    except Exception as e:
        logger.error(f"Failed to update status: {e}")
        st.error(f"Failed to update status: {str(e)}")


def edit_application_notes(app: Application, app_repo: ApplicationRepository):
    """
    Edit application notes
    
    Args:
        app: Application instance
        app_repo: Application repository instance
    """
    with st.form(f"edit_notes_form_{app.id}"):
        st.subheader("Edit Notes")
        
        new_notes = st.text_area(
            "Notes",
            value=app.notes,
            height=150,
            help="Add any notes about this application"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("💾 Save", use_container_width=True):
                app.notes = new_notes
                if app_repo.update(app):
                    st.success("✅ Notes updated!")
                    st.rerun()
                else:
                    st.error("Failed to update notes")
        
        with col2:
            if st.form_submit_button("❌ Cancel", use_container_width=True):
                st.rerun()


def delete_application(application_id: str, app_repo: ApplicationRepository):
    """
    Delete application
    
    Args:
        application_id: Application ID to delete
        app_repo: Application repository instance
    """
    try:
        if app_repo.delete(application_id):
            st.success("✅ Application deleted!")
            st.rerun()
        else:
            st.error("Failed to delete application")
    except Exception as e:
        logger.error(f"Failed to delete application: {e}")
        st.error(f"Failed to delete application: {str(e)}")


def view_job_details(job_id: str):
    """
    View job details (navigate to job search page)
    
    Args:
        job_id: Job ID to view
    """
    st.session_state.current_page = "Job Search"
    st.session_state.selected_job_id = job_id
    st.rerun()


def render_hr_contact_form(app_repo: ApplicationRepository, hr_repo: HRContactRepository):
    """
    Render HR contact form
    
    Args:
        app_repo: Application repository instance
        hr_repo: HR contact repository instance
    """
    if not st.session_state.selected_application_id:
        return
    
    st.subheader("👤 Manage HR Contact")
    
    # Get application
    app = app_repo.find_by_id(st.session_state.selected_application_id)
    
    if not app:
        st.error("Application not found")
        return
    
    # Check if HR contact already exists
    existing_contact = None
    if app.hr_contact_id:
        existing_contact = hr_repo.find_by_id(app.hr_contact_id)
    
    with st.form("hr_contact_form"):
        st.markdown("**Contact Information**")
        
        name = st.text_input(
            "Name *",
            value=existing_contact.name if existing_contact else "",
            help="HR contact's full name"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            email = st.text_input(
                "Email",
                value=existing_contact.email if existing_contact and existing_contact.email else "",
                help="HR contact's email address"
            )
        
        with col2:
            phone = st.text_input(
                "Phone",
                value=existing_contact.phone if existing_contact and existing_contact.phone else "",
                help="HR contact's phone number"
            )
        
        linkedin_url = st.text_input(
            "LinkedIn URL",
            value=existing_contact.linkedin_url if existing_contact and existing_contact.linkedin_url else "",
            help="HR contact's LinkedIn profile URL"
        )
        
        designation = st.text_input(
            "Designation",
            value=existing_contact.designation if existing_contact and existing_contact.designation else "",
            help="HR contact's job title"
        )
        
        notes = st.text_area(
            "Notes",
            value=existing_contact.notes if existing_contact else "",
            height=100,
            help="Any additional notes about this contact"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("💾 Save Contact", use_container_width=True):
                save_hr_contact(app, name, email, phone, linkedin_url, designation, notes, existing_contact, app_repo, hr_repo)
        
        with col2:
            if st.form_submit_button("❌ Cancel", use_container_width=True):
                st.session_state.show_hr_form = False
                st.session_state.selected_application_id = None
                st.rerun()


def save_hr_contact(
    app: Application,
    name: str,
    email: str,
    phone: str,
    linkedin_url: str,
    designation: str,
    notes: str,
    existing_contact: Optional[HRContact],
    app_repo: ApplicationRepository,
    hr_repo: HRContactRepository
):
    """
    Save HR contact information
    
    Args:
        app: Application instance
        name: Contact name
        email: Contact email
        phone: Contact phone
        linkedin_url: Contact LinkedIn URL
        designation: Contact designation
        notes: Contact notes
        existing_contact: Existing HR contact if updating
        app_repo: Application repository instance
        hr_repo: HR contact repository instance
    """
    try:
        if not name or not name.strip():
            st.error("Name is required")
            return
        
        if existing_contact:
            # Update existing contact
            existing_contact.name = name
            existing_contact.email = email if email else None
            existing_contact.phone = phone if phone else None
            existing_contact.linkedin_url = linkedin_url if linkedin_url else None
            existing_contact.designation = designation if designation else None
            existing_contact.notes = notes
            
            if hr_repo.update(existing_contact):
                st.success("✅ HR contact updated!")
                st.session_state.show_hr_form = False
                st.session_state.selected_application_id = None
                st.rerun()
            else:
                st.error("Failed to update HR contact")
        else:
            # Create new contact
            hr_contact = HRContact(
                application_id=app.id,
                name=name,
                email=email if email else None,
                phone=phone if phone else None,
                linkedin_url=linkedin_url if linkedin_url else None,
                designation=designation if designation else None,
                notes=notes
            )
            
            if hr_repo.save(hr_contact):
                # Update application with HR contact ID
                app.hr_contact_id = hr_contact.id
                if app_repo.update(app):
                    st.success("✅ HR contact saved!")
                    st.session_state.show_hr_form = False
                    st.session_state.selected_application_id = None
                    st.rerun()
                else:
                    st.error("Failed to link HR contact to application")
            else:
                st.error("Failed to save HR contact")
    
    except Exception as e:
        logger.error(f"Failed to save HR contact: {e}")
        st.error(f"Failed to save HR contact: {str(e)}")


def render_hr_directory(hr_repo: HRContactRepository, app_repo: ApplicationRepository, job_repo: JobRepository):
    """
    Render HR contact directory with search
    
    Args:
        hr_repo: HR contact repository instance
        app_repo: Application repository instance
        job_repo: Job repository instance
    """
    st.subheader("📇 HR Contact Directory")
    
    # Search bar
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input(
            "Search contacts",
            value=st.session_state.hr_search_query,
            placeholder="Search by name, email, or designation...",
            label_visibility="collapsed"
        )
        st.session_state.hr_search_query = search_query
    
    with col2:
        if st.button("🔍 Search", use_container_width=True):
            pass  # Search is already applied via text input
    
    # Get all HR contacts
    try:
        if search_query:
            # Search by name, email, or designation
            contacts = hr_repo.search({'name': search_query})
            email_contacts = hr_repo.search({'email': search_query})
            designation_contacts = hr_repo.search({'designation': search_query})
            
            # Combine and deduplicate
            all_contacts = contacts + email_contacts + designation_contacts
            contact_ids = set()
            unique_contacts = []
            for contact in all_contacts:
                if contact.id not in contact_ids:
                    contact_ids.add(contact.id)
                    unique_contacts.append(contact)
            
            contacts = unique_contacts
        else:
            contacts = hr_repo.find_all()
        
        if not contacts:
            st.info("No HR contacts found. Add contacts from the applications list.")
            return
        
        st.markdown(f"**{len(contacts)} contacts found**")
        st.markdown("---")
        
        # Display contacts
        for contact in contacts:
            render_hr_contact_card(contact, app_repo, job_repo, hr_repo)
    
    except Exception as e:
        logger.error(f"Failed to render HR directory: {e}")
        st.error("Failed to load HR directory")


def render_hr_contact_card(contact: HRContact, app_repo: ApplicationRepository, job_repo: JobRepository, hr_repo: HRContactRepository):
    """
    Render HR contact card
    
    Args:
        contact: HRContact instance
        app_repo: Application repository instance
        job_repo: Job repository instance
        hr_repo: HR contact repository instance
    """
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### {contact.name}")
            if contact.designation:
                st.markdown(f"**{contact.designation}**")
        
        with col2:
            if st.button("🗑️ Delete", key=f"delete_hr_{contact.id}", use_container_width=True):
                delete_hr_contact(contact.id, hr_repo)
        
        # Contact details
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if contact.email:
                st.markdown(f"📧 {contact.email}")
            else:
                st.markdown("📧 No email")
        
        with col2:
            if contact.phone:
                st.markdown(f"📱 {contact.phone}")
            else:
                st.markdown("📱 No phone")
        
        with col3:
            if contact.linkedin_url:
                st.markdown(f"[🔗 LinkedIn]({contact.linkedin_url})")
            else:
                st.markdown("🔗 No LinkedIn")
        
        # Associated application
        app = app_repo.find_by_id(contact.application_id)
        if app:
            job = job_repo.find_by_id(app.job_id)
            if job:
                st.markdown(f"**Associated with:** {job.title} at {job.company}")
        
        # Notes
        if contact.notes:
            with st.expander("📝 Notes"):
                st.markdown(contact.notes)
        
        st.markdown("---")


def delete_hr_contact(contact_id: str, hr_repo: HRContactRepository):
    """
    Delete HR contact
    
    Args:
        contact_id: Contact ID to delete
        hr_repo: HR contact repository instance
    """
    try:
        if hr_repo.delete(contact_id):
            st.success("✅ HR contact deleted!")
            st.rerun()
        else:
            st.error("Failed to delete HR contact")
    except Exception as e:
        logger.error(f"Failed to delete HR contact: {e}")
        st.error(f"Failed to delete HR contact: {str(e)}")


def export_applications(app_repo: ApplicationRepository, job_repo: JobRepository, hr_repo: HRContactRepository, format: str = "csv"):
    """
    Export applications to CSV or Excel
    
    Args:
        app_repo: Application repository instance
        job_repo: Job repository instance
        hr_repo: HR contact repository instance
        format: Export format ('csv' or 'excel')
    """
    try:
        # Get all applications
        applications = app_repo.find_by_user(st.session_state.user_id)
        
        if not applications:
            st.warning("No applications to export")
            return
        
        # Prepare data
        export_data = []
        
        for app in applications:
            job = job_repo.find_by_id(app.job_id)
            
            hr_name = ""
            hr_email = ""
            hr_phone = ""
            hr_linkedin = ""
            hr_designation = ""
            
            if app.hr_contact_id:
                hr_contact = hr_repo.find_by_id(app.hr_contact_id)
                if hr_contact:
                    hr_name = hr_contact.name
                    hr_email = hr_contact.email or ""
                    hr_phone = hr_contact.phone or ""
                    hr_linkedin = hr_contact.linkedin_url or ""
                    hr_designation = hr_contact.designation or ""
            
            export_data.append({
                'Job Title': job.title if job else "Unknown",
                'Company': job.company if job else "Unknown",
                'Status': app.status,
                'Applied Date': app.applied_date.strftime('%Y-%m-%d') if app.applied_date else "",
                'Interview Date': app.interview_date.strftime('%Y-%m-%d') if app.interview_date else "",
                'HR Name': hr_name,
                'HR Email': hr_email,
                'HR Phone': hr_phone,
                'HR LinkedIn': hr_linkedin,
                'HR Designation': hr_designation,
                'Notes': app.notes,
                'Job URL': job.source_url if job else ""
            })
        
        # Create DataFrame
        df = pd.DataFrame(export_data)
        
        # Export based on format
        if format == "csv":
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"applications_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        elif format == "excel":
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Applications')
            
            st.download_button(
                label="📥 Download Excel",
                data=buffer.getvalue(),
                file_name=f"applications_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    except Exception as e:
        logger.error(f"Failed to export applications: {e}")
        st.error(f"Failed to export applications: {str(e)}")


def render_applications():
    """Main applications page rendering function"""
    st.title("📝 Applications")
    st.markdown("Track your job applications, manage HR contacts, and monitor your progress!")
    st.markdown("---")
    
    try:
        # Initialize session state
        initialize_session_state()
        
        # Initialize repositories
        app_repo = ApplicationRepository(st.session_state.db_manager)
        hr_repo = HRContactRepository(st.session_state.db_manager)
        job_repo = JobRepository(st.session_state.db_manager)
        
        # Render statistics
        render_statistics(app_repo)
        
        st.markdown("---")
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📇 HR Directory", use_container_width=True):
                st.session_state.show_hr_directory = not st.session_state.show_hr_directory
                st.rerun()
        
        with col2:
            export_format = st.selectbox(
                "Export Format",
                options=["CSV", "Excel"],
                label_visibility="collapsed"
            )
        
        with col3:
            if st.button("📥 Export Applications", use_container_width=True):
                export_applications(app_repo, job_repo, hr_repo, export_format.lower())
        
        st.markdown("---")
        
        # Show HR form if requested
        if st.session_state.show_hr_form:
            render_hr_contact_form(app_repo, hr_repo)
            st.markdown("---")
        
        # Show HR directory if requested
        if st.session_state.show_hr_directory:
            render_hr_directory(hr_repo, app_repo, job_repo)
            st.markdown("---")
        
        # Render applications table
        render_applications_table(app_repo, job_repo, hr_repo)
        
    except Exception as e:
        logger.error(f"Applications page error: {e}", exc_info=True)
        st.error(f"Failed to load applications page: {str(e)}")
