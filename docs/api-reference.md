# API Reference

Complete API documentation for all mixins, methods, and fields in the Comprehensive Toolkit.

## 🎯 Ownable Mixin (`tk.ownable.mixin`)

### Fields

#### Core Fields
- **`owner_id`** (`Many2one`): Current owner of the record
  - Relation: `res.users`
  - Default: Current user
  - Tracking: Yes

- **`co_owner_ids`** (`Many2many`): Users who share ownership
  - Relation: `res.users`
  - Tracking: Yes

- **`previous_owner_id`** (`Many2one`): Previous owner before last transfer
  - Relation: `res.users`
  - Readonly: Yes

- **`ownership_date`** (`Datetime`): Date when current ownership was established
  - Default: Current datetime
  - Readonly: Yes

#### Computed Fields
- **`is_owned`** (`Boolean`): Whether record has an owner or co-owners
- **`can_transfer`** (`Boolean`): Whether current user can transfer ownership
- **`can_release`** (`Boolean`): Whether current user can release ownership
- **`can_manage_co_owners`** (`Boolean`): Whether current user can manage co-owners
- **`co_owner_count`** (`Integer`): Number of co-owners
- **`is_owned_by_me`** (`Boolean`): Whether current user owns or co-owns record

### Methods

#### `transfer_ownership(new_owner_id, reason=None)`
Transfer ownership to a new user.

**Parameters:**
- `new_owner_id` (int): ID of the new owner
- `reason` (str, optional): Reason for the transfer

**Returns:** `True` if successful

**Raises:**
- `AccessError`: If user lacks permission to transfer
- `ValidationError`: If new owner is invalid

**Example:**
```python
record.transfer_ownership(user.id, reason="Project handover")
```

#### `release_ownership(reason=None)`
Release current ownership, making the record unowned.

**Parameters:**
- `reason` (str, optional): Reason for releasing ownership

**Returns:** `True` if successful

**Raises:**
- `AccessError`: If user lacks permission to release

#### `claim_ownership(reason=None)`
Claim ownership of an unowned record.

**Parameters:**
- `reason` (str, optional): Reason for claiming ownership

**Returns:** `True` if successful

**Raises:**
- `ValidationError`: If record already has an owner

#### `add_co_owner(user_id, reason=None)`
Add a co-owner to the record.

**Parameters:**
- `user_id` (int): ID of user to add as co-owner
- `reason` (str, optional): Reason for adding co-owner

**Returns:** `True` if successful

#### `remove_co_owner(user_id, reason=None)`
Remove a co-owner from the record.

**Parameters:**
- `user_id` (int): ID of user to remove as co-owner
- `reason` (str, optional): Reason for removing co-owner

**Returns:** `True` if successful

---

## 🎯 Responsible Mixin (`tk.responsible.mixin`)

### Fields

#### Core Fields
- **`responsible_user_ids`** (`Many2many`): Users responsible for this record
- **`secondary_responsible_ids`** (`Many2many`): Users with secondary responsibility
- **`responsibility_start_date`** (`Datetime`): When responsibility was assigned
  - Default: Current datetime
  - Help: "Date when responsibility was assigned"

- **`responsibility_end_date`** (`Datetime`): When responsibility ends
  - Help: "Date when responsibility ends (for temporary responsibilities)"

- **`responsibility_delegated_by`** (`Many2one`): User who delegated responsibility
  - Relation: `res.users`
  - Readonly: Yes
  - Help: "User who delegated this responsibility"

- **`responsibility_description`** (`Text`): Description of responsibility
  - Help: "Description of what this responsibility entails"

#### Computed Fields
- **`is_responsibility_active`** (`Boolean`): Whether responsibility is currently active
- **`is_responsibility_expired`** (`Boolean`): Whether responsibility has expired
- **`can_delegate`** (`Boolean`): Whether current user can delegate responsibility
- **`responsibility_count`** (`Integer`): Number of responsible users
- **`secondary_responsibility_count`** (`Integer`): Number of secondary responsible users

### Methods

#### `assign_responsibility(user_ids, end_date=None, description=None, reason=None)`
Assign responsibility to users.

**Parameters:**
- `user_ids` (list): List of user IDs to assign responsibility to
- `end_date` (datetime, optional): When responsibility ends
- `description` (str, optional): Description of the responsibility
- `reason` (str, optional): Reason for assignment

**Returns:** `True` if successful

**Raises:**
- `AccessError`: If user lacks permission to assign
- `ValidationError`: If no users specified or invalid users

**Example:**
```python
record.assign_responsibility([user1.id, user2.id], 
                           end_date=fields.Datetime.now() + timedelta(days=30),
                           description="Review and approve document",
                           reason="Project milestone")
```

#### `assign_secondary_responsibility(user_ids, reason=None)`
Assign secondary responsibility to users.

**Parameters:**
- `user_ids` (list): List of user IDs to assign secondary responsibility to
- `reason` (str, optional): Reason for assignment

**Returns:** `True` if successful

#### `delegate_responsibility(user_ids, reason=None)`
Delegate responsibility to other users.

**Parameters:**
- `user_ids` (list): List of user IDs to delegate to
- `reason` (str, optional): Reason for delegation

**Returns:** `True` if successful

#### `transfer_responsibility(user_ids, reason=None)`
Transfer responsibility to other users (alias for delegate_responsibility).

**Parameters:**
- `user_ids` (list): List of user IDs to transfer to
- `reason` (str, optional): Reason for transfer

**Returns:** `True` if successful

#### `escalate_responsibility(escalation_user_id, reason=None)`
Escalate responsibility to a higher authority.

**Parameters:**
- `escalation_user_id` (int): ID of user to escalate to
- `reason` (str, optional): Reason for escalation

**Returns:** `True` if successful

#### `revoke_all_responsibility(reason=None)`
Revoke all responsibility from the record.

**Parameters:**
- `reason` (str, optional): Reason for revocation

**Returns:** `True` if successful

---

## 📋 Assignable Mixin (`tk.assignable.mixin`)

### Fields

#### Core Fields
- **`assigned_user_ids`** (`Many2many`): Users assigned to this record
  - Relation: `res.users`
  - Tracking: Yes

- **`assignment_date`** (`Datetime`): Date when assignment was made
  - Default: Current datetime

- **`assignment_deadline`** (`Datetime`): Deadline for the assignment

- **`assignment_description`** (`Text`): Description of the assignment

- **`assignment_priority`** (`Selection`): Priority level
  - Options: `low`, `normal`, `high`, `urgent`
  - Default: `normal`

#### Computed Fields
- **`is_assigned`** (`Boolean`): Whether record is assigned to users
- **`is_overdue`** (`Boolean`): Whether assignment is overdue
- **`can_assign`** (`Boolean`): Whether current user can assign
- **`assigned_count`** (`Integer`): Number of assigned users
- **`is_assigned_to_me`** (`Boolean`): Whether assigned to current user

### Methods

#### `assign_to_users(user_ids, deadline=None, description=None, priority='normal', reason=None)`
Assign the record to users.

#### `unassign_from_users(user_ids=None, reason=None)`
Unassign users from the record.

#### `reassign_to_users(user_ids, deadline=None, description=None, priority='normal', reason=None)`
Reassign the record to different users.

---

## 🔒 Accessible Mixin (`tk.accessible.mixin`)

### Fields

#### Core Fields
- **`access_level`** (`Selection`): Access level for the record
  - Options: `public`, `internal`, `restricted`, `private`
  - Default: `internal`
  - Tracking: Yes

- **`allowed_user_ids`** (`Many2many`): Users with explicit access
  - Relation: `res.users`

- **`allowed_group_ids`** (`Many2many`): System groups with access
  - Relation: `res.groups`

- **`custom_access_group_ids`** (`Many2many`): Custom access groups
  - Relation: `tk.accessible.group`

- **`access_start_date`** (`Datetime`): When access begins
- **`access_end_date`** (`Datetime`): When access expires

#### Computed Fields
- **`allowed_group_users_ids`** (`Many2many`): Users from allowed groups
  - Compute: `_compute_allowed_group_users_ids`
  - Store: Yes

- **`custom_group_users_ids`** (`Many2many`): Users from custom groups
  - Compute: `_compute_custom_group_users_ids`
  - Store: Yes

- **`all_allowed_users_ids`** (`Many2many`): All users with access
  - Compute: `_compute_all_allowed_users_ids`
  - Store: Yes

- **`is_access_expired`** (`Boolean`): Whether access has expired
  - Compute: `_compute_is_access_expired`

- **`can_grant_access`** (`Boolean`): Whether current user can grant access
  - Compute: `_compute_can_grant_access`

- **`has_access`** (`Boolean`): Whether current user has access
  - Compute: `_compute_has_access`

### Methods

#### Access Management for Users
- **`grant_access_to_user(user_id, start_date=None, end_date=None, reason=None)`**: Grant access to a user
- **`revoke_access_from_user(user_id, reason=None)`**: Revoke access from a user
- **`bulk_grant_access_to_users(user_ids, start_date=None, end_date=None, reason=None)`**: Grant access to multiple users
- **`bulk_revoke_access_from_users(user_ids, reason=None)`**: Revoke access from multiple users

#### Access Management for Groups
- **`grant_access_to_group(group_id, start_date=None, end_date=None, reason=None)`**: Grant access to a system group
- **`revoke_access_from_group(group_id, reason=None)`**: Revoke access from a system group
- **`grant_access_to_custom_group(custom_group_id, start_date=None, end_date=None, reason=None)`**: Grant access to a custom group
- **`revoke_access_from_custom_group(custom_group_id, reason=None)`**: Revoke access from a custom group

#### Group Creation and Management
- **`create_and_assign_custom_group(group_name, user_ids, group_type='custom', reason=None)`**: Create and assign new custom group

#### Access Control
- **`set_access_level(level, reason=None)`**: Set the access level
- **`set_access_duration(start_date=None, end_date=None, reason=None)`**: Set access duration
- **`get_all_accessible_users()`**: Get all users with access
- **`check_user_has_access(user_id)`**: Check if user has access

#### Access Level Logic

1. **Public**: Everyone has access (including portal users)
2. **Internal**: All internal users have access (group_user)
3. **Restricted**: Only explicit users, allowed groups, and custom groups have access
4. **Private**: Only explicit users and custom groups have access (no system groups)

Special access rules:
- System administrators always have access
- Record owners always have access (if using ownable mixin)
- Co-owners always have access (if using ownable mixin)
- Access can be time-limited with start/end dates
- Expired access is automatically denied

---

## 🔒 Accessible Group Mixin (`tk.accessible.group.mixin`)

### Fields

#### Enhanced Group Management
- **`allowed_group_users_ids`** (`Many2many`): All users from system and custom groups
- **`custom_access_group_ids`** (`Many2many`): Custom access groups with enhanced functionality
- **`can_manage_groups`** (`Boolean`): Whether current user can manage groups
- **`total_group_users_count`** (`Integer`): Total users with group access
- **`active_custom_groups_count`** (`Integer`): Number of active custom groups
- **`has_group_access`** (`Boolean`): Whether current user has group access

### Methods

#### Custom Group Management
- **`add_custom_access_group(group_id, reason=None)`**: Add custom group to record
- **`remove_custom_access_group(group_id, reason=None)`**: Remove custom group from record
- **`replace_custom_access_groups(group_ids, reason=None)`**: Replace all custom groups
- **`clear_all_custom_groups(reason=None)`**: Remove all custom groups

#### Group Information
- **`get_users_from_group(group_id)`**: Get users from specific group
- **`get_all_group_users(include_inactive=False)`**: Get all users from all groups
- **`check_user_group_access(user=None)`**: Check if user has group access
- **`get_group_access_summary()`**: Get detailed group access summary

#### Actions
- **`action_manage_custom_groups()`**: Open wizard to manage custom groups
- **`action_view_group_users()`**: View all users with group access

---

## 📊 Models

### Custom Access Group (`tk.accessible.group`)

#### Fields
- **`name`** (`Char`): Group name
- **`description`** (`Text`): Group description
- **`group_type`** (`Selection`): Type of group
  - Options: `project`, `department`, `temporary`, `custom`
- **`user_ids`** (`Many2many`): Users in the group
- **`active`** (`Boolean`): Whether group is active
- **`user_count`** (`Integer`): Number of users (computed)

#### Methods
- **`add_users(user_ids, reason=None)`**: Add users to group
- **`remove_users(user_ids, reason=None)`**: Remove users from group
- **`toggle_active()`**: Toggle active state
- **`create_project_team_group(project_name, user_ids)`**: Create project team group
- **`create_department_group(department_name, user_ids)`**: Create department group

### Access Log (`tk.access.log`)

#### Fields
- **`model_name`** (`Char`): Model of the record
- **`res_id`** (`Integer`): ID of the record
- **`record_reference`** (`Char`): Display name of record (computed)
- **`action`** (`Selection`): Type of access change
- **`target_user_id`** (`Many2one`): Target user (if applicable)
- **`target_group_id`** (`Many2one`): Target group (if applicable)
- **`target_custom_group_id`** (`Many2one`): Target custom group (if applicable)
- **`user_id`** (`Many2one`): User who made the change
- **`date`** (`Datetime`): When change occurred
- **`reason`** (`Text`): Reason for change
- **`extra_info`** (`Text`): Additional information
- **`display_name`** (`Char`): Formatted display name (computed)

#### Methods
- **`open_record()`**: Open the referenced record
- **`cleanup_old_logs(days=90)`**: Clean up old log entries

---

## 🧙‍♂️ Wizards

### Access Management Wizards

#### Bulk Access Wizard (`tk.bulk.access.wizard`)
- Bulk update access control for multiple records
- Set access levels, permissions, and duration
- Support for users, groups, and custom groups

#### Manage Access Wizard (`tk.manage.access.wizard`)
- Manage access for individual records
- Complete access control configuration
- User-friendly interface for permissions

#### Accessible Group Wizard (`tk.accessible.group.wizard`)
- Create and configure custom access groups
- Template-based group creation
- Project, department, and temporary group types
- User and manager assignment
- Copy from existing groups functionality

### Key Features

#### Template Types
- **Project Team Template**: Pre-configured for project teams
- **Department Team Template**: Department-based access
- **External Partners Template**: External user access
- **Temporary Access Template**: Time-limited access groups

#### Group Types
- **General**: General purpose access groups
- **Project**: Project team access groups
- **Department**: Department-based groups
- **Temporary**: Time-limited groups with expiry
- **External**: External user groups
- **Custom**: Fully customizable groups

#### Visibility Levels
- **Public**: Anyone can see the group
- **Internal**: Internal users can see
- **Restricted**: Only managers can see
- **Private**: Only creator can see

---

## 🔍 Search Methods

All mixins provide search methods for their computed fields:
- `_search_can_delegate()` - Search records where user can delegate responsibility
- `_search_can_transfer()` - Search records where user can transfer ownership
- `_search_can_assign()` - Search records where user can assign users
- `_search_can_access()` - Search records where user has access

---

## 🎨 Integration Examples

### Using Multiple Mixins Together

```python
class ProjectDocument(models.Model):
    _name = 'project.document'
    _inherit = [
        'tk.ownable.mixin',
        'tk.responsible.mixin', 
        'tk.assignable.mixin',
        'tk.accessible.mixin',
        'tk.accessible.group.mixin'
    ]
    
    name = fields.Char(required=True)
    content = fields.Html()
    
    def setup_project_access(self, project_team_users):
        # Create project team group
        team_group = self.create_and_assign_custom_group(
            group_name=f"Project Team - {self.name}",
            user_ids=project_team_users.ids,
            group_type='project'
        )
        
        # Set restricted access
        self.set_access_level('restricted')
        
        # Assign responsibility to project lead
        lead = project_team_users.filtered('is_project_lead')[:1]
        if lead:
            self.assign_responsibility([lead.id])
```

### Bulk Operations

```python
# Bulk access management
documents = self.env['project.document'].search([('project_id', '=', project.id)])

# Create shared access group
shared_group = self.env['tk.accessible.group'].create({
    'name': f'Project {project.name} Access',
    'group_type': 'project',
    'user_ids': [(6, 0, project.team_member_ids.ids)]
})

# Apply to all documents
for doc in documents:
    doc.grant_access_to_custom_group(shared_group.id, reason="Project access setup")
```
