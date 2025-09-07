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
  - Compute: `_compute_is_owned`
  - Store: Yes
  - Depends: `owner_id`, `co_owner_ids`

- **`can_transfer`** (`Boolean`): Whether current user can transfer ownership
  - Compute: `_compute_can_transfer`
  - Depends: `owner_id`

- **`can_release`** (`Boolean`): Whether current user can release ownership
  - Compute: `_compute_can_release`
  - Depends: `owner_id`

- **`can_manage_co_owners`** (`Boolean`): Whether current user can manage co-owners
  - Compute: `_compute_can_manage_co_owners`
  - Depends: `owner_id`, `co_owner_ids`

- **`co_owner_count`** (`Integer`): Number of co-owners
  - Compute: `_compute_co_owner_count`
  - Depends: `co_owner_ids`

- **`is_owned_by_me`** (`Boolean`): Whether current user owns or co-owns record
  - Compute: `_compute_is_owned_by_me`
  - Depends: `owner_id`, `co_owner_ids`

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

**Raises:**
- `AccessError`: If user lacks permission
- `ValidationError`: If user is invalid or already a co-owner

#### `remove_co_owner(user_id, reason=None)`
Remove a co-owner from the record.

**Parameters:**
- `user_id` (int): ID of user to remove
- `reason` (str, optional): Reason for removal

**Returns:** `True` if successful

#### `add_multiple_co_owners(user_ids, reason=None)`
Add multiple co-owners at once.

**Parameters:**
- `user_ids` (list): List of user IDs to add
- `reason` (str, optional): Reason for adding co-owners

**Returns:** `True` if successful

#### `remove_all_co_owners(reason=None)`
Remove all co-owners from the record.

**Parameters:**
- `reason` (str, optional): Reason for removal

**Returns:** `True` if successful

#### `is_owner_or_co_owner(user=None)`
Check if a user is the owner or a co-owner.

**Parameters:**
- `user` (recordset, optional): User to check (defaults to current user)

**Returns:** `Boolean`

#### `get_all_owners()`
Get all owners (owner + co-owners) as a recordset.

**Returns:** `res.users` recordset

---

## 📋 Assignable Mixin (`tk.assignable.mixin`)

### Fields

#### Core Fields
- **`assigned_user_ids`** (`Many2many`): Users assigned to this record
  - Relation: `res.users`
  - Tracking: Yes

- **`assigner_id`** (`Many2one`): User who made the assignment
  - Relation: `res.users`
  - Readonly: Yes

- **`assignment_date`** (`Datetime`): Date when assignment was made
  - Readonly: Yes

- **`assignment_deadline`** (`Datetime`): Deadline for completing assignment

- **`assignment_status`** (`Selection`): Current assignment status
  - Options: `unassigned`, `assigned`, `in_progress`, `completed`, `cancelled`
  - Default: `unassigned`
  - Tracking: Yes

- **`assignment_description`** (`Text`): Description of assignment

- **`assignment_priority`** (`Selection`): Assignment priority
  - Options: `low`, `normal`, `high`, `urgent`
  - Default: `normal`
  - Tracking: Yes

#### Computed Fields
- **`is_assigned`** (`Boolean`): Whether record is assigned to someone
  - Compute: `_compute_is_assigned`
  - Store: Yes
  - Depends: `assigned_user_ids`

- **`is_overdue`** (`Boolean`): Whether assignment is overdue
  - Compute: `_compute_is_overdue`
  - Depends: `assignment_deadline`

- **`can_assign`** (`Boolean`): Whether current user can assign this record
  - Compute: `_compute_can_assign`

- **`assigned_user_count`** (`Integer`): Number of assigned users
  - Compute: `_compute_assigned_user_count`
  - Depends: `assigned_user_ids`

- **`is_assigned_to_me`** (`Boolean`): Whether current user is assigned
  - Compute: `_compute_is_assigned_to_me`
  - Depends: `assigned_user_ids`

### Methods

#### `assign_to_users(user_ids, deadline=None, description=None, priority='normal', reason=None)`
Assign record to multiple users.

**Parameters:**
- `user_ids` (list): List of user IDs to assign
- `deadline` (datetime, optional): Assignment deadline
- `description` (str, optional): Assignment description
- `priority` (str, optional): Assignment priority
- `reason` (str, optional): Reason for assignment

**Returns:** `True` if successful

#### `add_assignee(user_id, reason=None)`
Add an assignee to the record.

**Parameters:**
- `user_id` (int): ID of user to assign
- `reason` (str, optional): Reason for assignment

**Returns:** `True` if successful

#### `remove_assignee(user_id, reason=None)`
Remove an assignee from the record.

**Parameters:**
- `user_id` (int): ID of user to remove
- `reason` (str, optional): Reason for removal

**Returns:** `True` if successful

#### `unassign_all_users(reason=None)`
Remove all assignees from the record.

**Parameters:**
- `reason` (str, optional): Reason for unassignment

**Returns:** `True` if successful

#### `start_assignment(reason=None)`
Start the assignment (change status to in_progress).

**Parameters:**
- `reason` (str, optional): Reason for starting

**Returns:** `True` if successful

#### `complete_assignment(reason=None)`
Complete the assignment (change status to completed).

**Parameters:**
- `reason` (str, optional): Reason for completion

**Returns:** `True` if successful

#### `cancel_assignment(reason=None)`
Cancel the assignment (change status to cancelled).

**Parameters:**
- `reason` (str, optional): Reason for cancellation

**Returns:** `True` if successful

---

## 🔐 Accessible Mixin (`tk.accessible.mixin`)

### Fields

#### Core Fields
- **`access_level`** (`Selection`): Access level for this record
  - Options: `public`, `internal`, `restricted`, `private`
  - Default: `internal`
  - Tracking: Yes

- **`allowed_user_ids`** (`Many2many`): Users with explicit access
  - Relation: `res.users`

- **`allowed_group_ids`** (`Many2many`): Groups with access
  - Relation: `res.groups`

- **`custom_access_group_ids`** (`Many2many`): Custom access groups
  - Relation: `tk.accessible.group`

- **`access_start_date`** (`Datetime`): Date from which access is granted

- **`access_end_date`** (`Datetime`): Date until which access is granted

#### Computed Fields
- **`allowed_group_users_ids`** (`Many2many`): Users from allowed groups
  - Compute: `_compute_allowed_group_users_ids`
  - Store: Yes
  - Depends: `allowed_group_ids`

- **`custom_group_users_ids`** (`Many2many`): Users from custom groups
  - Compute: `_compute_custom_group_users_ids`
  - Store: Yes
  - Depends: `custom_access_group_ids`

- **`all_allowed_users_ids`** (`Many2many`): All users with access
  - Compute: `_compute_all_allowed_users_ids`
  - Store: Yes

- **`is_access_expired`** (`Boolean`): Whether access has expired
  - Compute: `_compute_is_access_expired`
  - Depends: `access_end_date`

- **`can_grant_access`** (`Boolean`): Whether current user can grant access
  - Compute: `_compute_can_grant_access`

- **`has_access`** (`Boolean`): Whether current user has access
  - Compute: `_compute_has_access`

### Methods

#### `grant_access(user_ids, reason=None)`
Grant access to specific users.

**Parameters:**
- `user_ids` (list): List of user IDs to grant access
- `reason` (str, optional): Reason for granting access

**Returns:** `True` if successful

#### `revoke_access(user_ids, reason=None)`
Revoke access from specific users.

**Parameters:**
- `user_ids` (list): List of user IDs to revoke access
- `reason` (str, optional): Reason for revoking access

**Returns:** `True` if successful

#### `grant_group_access(group_id, reason=None)`
Grant access to an Odoo group.

**Parameters:**
- `group_id` (int): ID of group to grant access
- `reason` (str, optional): Reason for granting access

**Returns:** `True` if successful

#### `revoke_group_access(group_id, reason=None)`
Revoke access from an Odoo group.

**Parameters:**
- `group_id` (int): ID of group to revoke access
- `reason` (str, optional): Reason for revoking access

**Returns:** `True` if successful

#### `set_access_level(level, reason=None)`
Set the access level for the record.

**Parameters:**
- `level` (str): Access level (`public`, `internal`, `restricted`, `private`)
- `reason` (str, optional): Reason for change

**Returns:** `True` if successful

#### `check_user_access(user=None)`
Check if a user has access to the record.

**Parameters:**
- `user` (recordset, optional): User to check (defaults to current user)

**Returns:** `Boolean`

#### `copy_access_from(source_record, reason=None)`
Copy access permissions from another record.

**Parameters:**
- `source_record` (recordset): Record to copy permissions from
- `reason` (str, optional): Reason for copying

**Returns:** `True` if successful

---

## 👥 Responsible Mixin (`tk.responsible.mixin`)

### Fields

#### Core Fields
- **`responsible_user_ids`** (`Many2many`): Users responsible for this record
  - Relation: `res.users`
  - Tracking: Yes

- **`secondary_responsible_ids`** (`Many2many`): Users with secondary responsibility
  - Relation: `res.users`
  - Tracking: Yes

- **`responsibility_type`** (`Selection`): Type of responsibility
  - Options: `primary`, `secondary`, `backup`, `temporary`
  - Default: `primary`
  - Tracking: Yes

- **`responsibility_start_date`** (`Datetime`): When responsibility was assigned
  - Default: Current datetime

- **`responsibility_end_date`** (`Datetime`): When responsibility ends

- **`responsibility_delegated_by`** (`Many2one`): User who delegated responsibility
  - Relation: `res.users`
  - Readonly: Yes

- **`responsibility_description`** (`Text`): Description of responsibilities

#### Computed Fields
- **`is_responsibility_active`** (`Boolean`): Whether responsibility is active
  - Compute: `_compute_is_responsibility_active`
  - Store: Yes
  - Depends: `responsible_user_ids`, `responsibility_end_date`

- **`is_responsibility_expired`** (`Boolean`): Whether responsibility has expired
  - Compute: `_compute_is_responsibility_expired`
  - Depends: `responsibility_end_date`

- **`can_delegate`** (`Boolean`): Whether current user can delegate responsibility
  - Compute: `_compute_can_delegate`

- **`responsibility_count`** (`Integer`): Number of responsible users
  - Compute: `_compute_responsibility_count`
  - Depends: `responsible_user_ids`

### Methods

#### `assign_responsibility(user_ids, responsibility_type='primary', description=None, end_date=None, reason=None)`
Assign responsibility to users.

**Parameters:**
- `user_ids` (list): List of user IDs to make responsible
- `responsibility_type` (str, optional): Type of responsibility
- `description` (str, optional): Description of responsibilities
- `end_date` (datetime, optional): When responsibility ends
- `reason` (str, optional): Reason for assignment

**Returns:** `True` if successful

#### `delegate_responsibility(user_id, end_date=None, reason=None)`
Delegate responsibility to another user.

**Parameters:**
- `user_id` (int): ID of user to delegate to
- `end_date` (datetime, optional): When delegation ends
- `reason` (str, optional): Reason for delegation

**Returns:** `True` if successful

#### `remove_responsibility(user_id, reason=None)`
Remove responsibility from a user.

**Parameters:**
- `user_id` (int): ID of user to remove responsibility from
- `reason` (str, optional): Reason for removal

**Returns:** `True` if successful

#### `transfer_responsibility(old_user_id, new_user_id, reason=None)`
Transfer responsibility from one user to another.

**Parameters:**
- `old_user_id` (int): ID of current responsible user
- `new_user_id` (int): ID of new responsible user
- `reason` (str, optional): Reason for transfer

**Returns:** `True` if successful

#### `add_secondary_responsible(user_ids, reason=None)`
Add users as secondary responsible.

**Parameters:**
- `user_ids` (list): List of user IDs to add
- `reason` (str, optional): Reason for addition

**Returns:** `True` if successful

---

## 🏗️ Supporting Models

### Custom Access Group (`tk.accessible.group`)

#### Fields
- **`name`** (`Char`): Group name (required)
- **`description`** (`Text`): Group description
- **`user_ids`** (`Many2many`): Users in this group
- **`active`** (`Boolean`): Whether group is active (default: True)

#### Methods

#### `add_users(user_ids)`
Add users to the access group.

#### `remove_users(user_ids)`
Remove users from the access group.

### Dashboard (`tk.comprehensive.dashboard`)

#### Fields
- **`date_from`** (`Date`): Start date for statistics
- **`date_to`** (`Date`): End date for statistics
- Various computed statistics fields for each mixin

#### Methods

#### `refresh_statistics()`
Refresh all computed statistics.

---

## 📊 Log Models

### Ownership Log (`tk.ownership.log`)
Tracks all ownership changes.

#### Fields
- **`model_name`** (`Char`): Model name of the record
- **`res_id`** (`Integer`): ID of the record
- **`action`** (`Selection`): Type of action performed
- **`old_owner_id`** (`Many2one`): Previous owner
- **`new_owner_id`** (`Many2one`): New owner
- **`reason`** (`Text`): Reason for the change
- **`user_id`** (`Many2one`): User who performed the action
- **`date`** (`Datetime`): When the action occurred

### Assignment Log (`tk.assignment.log`)
Tracks all assignment activities.

### Access Log (`tk.access.log`)
Tracks access permission changes.

### Responsibility Log (`tk.responsibility.log`)
Tracks responsibility changes.

---

## 🔍 Search Methods

### Domain Helpers

#### `_get_ownership_domain()`
Returns domain for records owned by current user.

#### `_get_assignment_domain()`
Returns domain for records assigned to current user.

#### `_get_accessible_domain()`
Returns domain for records accessible to current user.

#### `_get_responsibility_domain()`
Returns domain for records user is responsible for.

---

## 🚨 Exceptions

### Custom Exceptions
- **`OwnershipError`**: Raised for ownership-related issues
- **`AssignmentError`**: Raised for assignment-related issues
- **`AccessError`**: Raised for access permission issues
- **`ResponsibilityError`**: Raised for responsibility-related issues

---

## 🔧 Utility Functions

### Permission Checking
- **`has_ownership_permission(record, user, action)`**: Check ownership permissions
- **`has_assignment_permission(record, user, action)`**: Check assignment permissions
- **`has_access_permission(record, user, action)`**: Check access permissions
- **`has_responsibility_permission(record, user, action)`**: Check responsibility permissions

### Logging Helpers
- **`log_ownership_change()`**: Log ownership changes
- **`log_assignment_change()`**: Log assignment changes
- **`log_access_change()`**: Log access changes
- **`log_responsibility_change()`**: Log responsibility changes

---

**Note**: All methods that modify data include audit logging automatically. All computed fields are cached for performance and updated when dependencies change.
