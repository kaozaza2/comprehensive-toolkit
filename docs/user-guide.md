# User Guide

This comprehensive guide covers how to use all features of the Comprehensive Toolkit module in your daily Odoo workflows.

## 🎯 Overview

The Comprehensive Toolkit provides four powerful mixins that can be inherited by any Odoo model to add advanced management capabilities:

1. **Ownership Management** - Track and manage record ownership
2. **Assignment Management** - Assign records to users with tracking
3. **Access Control** - Manage who can access records with flexible permissions
4. **Responsibility Management** - Define and track responsibilities

## 🏠 Getting Started

### Accessing the Dashboard

1. Navigate to **Comprehensive Toolkit** in the main menu
2. Click **Dashboard** to see overview statistics
3. Use date filters to view activity for specific periods

The dashboard shows:
- Total activity counts across all features
- Your personal assignments and responsibilities
- Recent activity summaries
- Overdue items requiring attention

## 👤 Ownership Management

### Understanding Ownership

Every record can have:
- **One Owner**: Primary owner with full control
- **Multiple Co-owners**: Additional users with ownership rights
- **Previous Owner**: Tracked for audit purposes

### Basic Ownership Operations

#### Viewing Ownership Information
On any record with ownership capabilities, you'll see:
- **Owner**: Current primary owner
- **Co-owners**: List of co-owners
- **Ownership Date**: When current ownership was established
- **Previous Owner**: Who owned it before

#### Transferring Ownership
1. Open a record you own
2. Click **Action → Transfer Ownership**
3. Select the new owner
4. Provide a reason (optional but recommended)
5. Click **Transfer**

#### Adding Co-owners
1. Open a record you own
2. Click **Action → Add Co-owner**
3. Select user(s) to add as co-owners
4. Provide a reason
5. Click **Add**

#### Releasing Ownership
1. Open a record you own
2. Click **Action → Release Ownership**
3. Provide a reason
4. Click **Release**

The record becomes unowned and can be claimed by others.

#### Claiming Ownership
1. Find an unowned record
2. Click **Action → Claim Ownership**
3. Provide a reason
4. Click **Claim**

## 📋 Assignment Management

### Understanding Assignments

Records can be assigned to multiple users with:
- **Assignment Status**: Unassigned, Assigned, In Progress, Completed, Cancelled
- **Priority Levels**: Low, Normal, High, Urgent
- **Deadlines**: Due dates with overdue tracking
- **Descriptions**: Detailed task descriptions

### Assignment Operations

#### Assigning Records
1. Open a record you can assign
2. Click **Action → Assign to Users**
3. Select users to assign
4. Set deadline and priority
5. Add description
6. Click **Assign**

#### Managing Assignments
- **Update Status**: Change assignment status as work progresses
- **Reassign**: Transfer assignment to different users
- **Unassign**: Remove assignment from users
- **Extend Deadline**: Update due dates

## 🎯 Responsibility Management

### Understanding Responsibility

Responsibility management allows you to:
- **Assign Primary Responsibility**: Main responsible users
- **Assign Secondary Responsibility**: Supporting responsible users
- **Set Temporary Responsibility**: With end dates
- **Track Responsibility Changes**: Full audit trail

### Key Concepts

#### Types of Responsibility
- **Primary Responsibility**: Main users accountable for the record
- **Secondary Responsibility**: Supporting users with backup accountability
- **Temporary Responsibility**: Time-limited responsibility with end dates
- **Escalated Responsibility**: Responsibility moved to higher authority

#### Responsibility Permissions
Users can delegate responsibility if they:
- Are currently responsible (primary or secondary)
- Own the record (if using ownership mixin)
- Have appropriate access permissions
- Are system administrators

### Basic Responsibility Operations

#### Assigning Responsibility
1. Open a record you can manage
2. Click **Action → Assign Responsibility**
3. Select responsible users
4. Choose if secondary responsibility
5. Set end date (optional)
6. Add description and reason
7. Click **Assign**

#### Transferring Responsibility
1. Open a record where you're responsible
2. Click **Action → Transfer Responsibility**
3. Choose transfer type:
   - **Transfer**: Move responsibility to new users
   - **Delegate**: Share responsibility with new users
   - **Escalate**: Move to higher authority (single user)
4. Select target users
5. Provide reason
6. Click **Transfer**

#### Revoking Responsibility
1. Open a record where you can manage responsibility
2. Click **Action → Revoke Responsibility**
3. Choose revocation type:
   - **All Responsibility**: Remove all responsible users
   - **Primary Only**: Remove only primary responsible users
   - **Secondary Only**: Remove only secondary responsible users
4. Provide reason (required)
5. Click **Revoke**

## 🔒 Access Control

### Understanding Access Levels

Records can have different access levels:
- **Public**: Everyone has access (including portal users)
- **Internal**: All internal users have access (default)
- **Restricted**: Only specific users, groups, and custom groups have access
- **Private**: Only specific users and custom groups have access (no system groups)

### Access Control Components

#### Direct User Access
- **Allowed Users**: Specific users granted explicit access
- Grant or revoke access for individual users
- Set time-limited access with start and end dates

#### System Group Access
- **Allowed Groups**: Odoo system groups with access
- Leverage existing security groups
- Automatic user inclusion based on group membership

#### Custom Access Groups
- **Custom Groups**: Flexible, project-specific access groups
- Create groups for projects, departments, or temporary access
- Manage group membership independently

### Managing Access

#### Setting Access Level
1. Open a record you can manage
2. Go to **Access Control** tab
3. Select desired access level:
   - **Public**: Open to everyone
   - **Internal**: All internal users
   - **Restricted**: Configured permissions only
   - **Private**: Most restrictive
4. Save changes

#### Granting Access to Users
1. In the **Access Control** tab
2. Add users to **Allowed Users** field
3. Optionally set **Access Start Date** and **Access End Date**
4. Provide reason for the change
5. Save

#### Using System Groups
1. Add groups to **Allowed Groups** field
2. All members of those groups automatically get access
3. Useful for department-wide or role-based access

#### Managing Custom Access Groups

##### Creating Custom Groups
1. Navigate to **Comprehensive Toolkit → Configuration → Access Groups**
2. Click **Create**
3. Fill in group details:
   - **Name**: Descriptive group name
   - **Type**: Project, Department, Temporary, or Custom
   - **Description**: Purpose of the group
4. Add users to the group
5. Save

##### Using the Group Creation Wizard
1. Click **Action → Create Access Group** on any record
2. Choose operation type:
   - **Create New Group**: Start from scratch
   - **Assign Existing Group**: Use existing group
   - **Manage Users**: Modify group membership
   - **Bulk Assign**: Apply multiple groups
3. Configure group settings:
   - **Template Types**: Use pre-configured templates
   - **Group Types**: Project, Department, Temporary, External, Custom
   - **Visibility Levels**: Control who can see the group
4. Add users and managers
5. Click **Create Group**

##### Template-Based Group Creation
Available templates:
- **Project Team Template**: Pre-configured for project teams
- **Department Team Template**: Department-based access
- **External Partners Template**: External user access
- **Temporary Access Template**: Time-limited access groups

##### Advanced Group Features
- **Group Managers**: Users who can manage the group
- **Temporary Groups**: Automatically expire after set date
- **Copy from Existing**: Duplicate user list from another group
- **Auto-add Creator**: Automatically add group creator as manager

#### Bulk Access Operations
1. Select multiple records in list view
2. Click **Action → Bulk Access Control**
3. Choose access level and permissions
4. Configure users, groups, and custom groups
5. Set access duration if needed
6. Provide reason
7. Click **Update Access**

### Access Duration and Expiry

#### Time-Limited Access
- Set **Access Start Date** for future access
- Set **Access End Date** for automatic expiry
- System automatically denies expired access
- Use for temporary projects or contractor access

#### Managing Expired Access
- Filter records by "Access Expired"
- Review and renew access as needed
- System notifications for upcoming expiries

### Access Control Best Practices

1. **Use Appropriate Access Levels**
   - Start with Internal for most records
   - Use Restricted for sensitive information
   - Use Private for highly confidential data

2. **Leverage Custom Groups**
   - Create project-specific groups
   - Use department groups for ongoing access
   - Set up temporary groups for short-term access

3. **Set Access Duration**
   - Use time-limited access for contractors
   - Set expiry dates for project-based access
   - Review access permissions regularly

4. **Document Access Changes**
   - Always provide meaningful reasons
   - Use descriptive group names
   - Maintain clear access policies

## 📊 Activity Monitoring

### Viewing Logs

All activities are logged and can be viewed:

#### Access Logs
- Navigate to **Comprehensive Toolkit → Logs → Access Logs**
- Track all access permission changes
- Filter by action type:
  - **Grant Access**: User and group grants
  - **Revoke Access**: User and group revocations
  - **Access Changes**: Level and duration changes
- Group by model, user, or date
- Search by reason or target

#### Other Log Types
- **Ownership Logs**: Track ownership changes
- **Responsibility Logs**: Monitor responsibility assignments
- **Assignment Logs**: Track assignment activities

### Using Filters and Search

Each log view provides:
- **Date Filters**: Today, this week, this month
- **Action Filters**: Specific action types
- **User Filters**: Activities by specific users
- **My Actions**: Your own activities
- **Advanced Search**: Full-text search capabilities

## 🎛️ Dashboard Features

### Overview Statistics
- **Total Records**: Count of managed records
- **Active Assignments**: Current assignments across system
- **Recent Activity**: Latest changes and updates
- **My Responsibilities**: Your current responsibilities
- **Access Groups**: Custom group statistics
- **Overdue Items**: Items requiring attention

### Interactive Elements
- Click statistics to drill down to detailed views
- Use date pickers to filter timeframes
- Access quick actions from dashboard cards
- View trending data and activity patterns

## 💡 Best Practices

### Access Control Management
1. **Principle of Least Privilege**: Grant minimum necessary access
2. **Use Custom Groups**: Create project and department-specific groups
3. **Set Access Duration**: Use time-limited access when appropriate
4. **Regular Reviews**: Periodically audit access permissions
5. **Document Changes**: Always provide clear reasons for access changes

### Group Management
1. **Descriptive Names**: Use clear, descriptive group names
2. **Appropriate Types**: Choose correct group type for purpose
3. **Manager Assignment**: Assign group managers for delegation
4. **Regular Cleanup**: Archive unused or expired groups
5. **Template Usage**: Use templates for consistent group setup

### Integration with Other Features
1. **Ownership + Access**: Owners automatically have access
2. **Responsibility + Access**: Assign access with responsibility
3. **Assignment + Access**: Ensure assigned users have access
4. **Bulk Operations**: Use for efficient permission management

## 🔧 Troubleshooting

### Common Access Issues

#### "Access Denied" Errors
- Check record access level settings
- Verify you're in allowed users or groups
- Check if access has expired
- Contact record owner for access

#### "Cannot Manage Access Groups"
- Ensure you have management permissions
- Check if you're group owner or manager
- Verify system administrator rights
- Review record ownership status

#### "Group Not Visible"
- Check group visibility level
- Verify group is active
- Ensure you have permission to see group
- Contact group creator or manager

#### "Access Expired"
- Check access end date settings
- Request access renewal from owner
- Review group expiry settings
- Update access duration if needed

### Getting Help
- Check access logs for detailed information
- Review permission settings and group membership
- Contact system administrators for complex issues
- Refer to API documentation for technical details

## 📝 Quick Reference

### Keyboard Shortcuts
- **Ctrl+A**: Select all records in list view
- **Ctrl+Click**: Multi-select records
- **F5**: Refresh current view

### Common Workflows
1. **Project Setup**: Create Group → Assign Access → Set Responsibility → Configure Ownership
2. **Team Collaboration**: Create Custom Group → Add Team Members → Grant Project Access
3. **Temporary Access**: Create Temporary Group → Set Expiry → Grant Limited Access
4. **Access Review**: Filter by Groups → Review Members → Update Permissions
5. **Bulk Operations**: Select Records → Apply Access Level → Configure Groups

This completes the comprehensive user guide for the Comprehensive Toolkit module with detailed access control functionality.
