# API Reference

## Core Mixins API

### `tk.ownable.mixin`

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `owner_id` | Many2one('res.users') | Current owner of the record |
| `co_owner_ids` | Many2many('res.users') | Users who share ownership |
| `previous_owner_id` | Many2one('res.users') | Previous owner before last transfer |
| `ownership_date` | Datetime | When current ownership was established |
| `is_owned` | Boolean (computed) | Whether record has an owner |
| `can_transfer` | Boolean (computed) | Whether current user can transfer ownership |
| `can_release` | Boolean (computed) | Whether current user can release ownership |
| `can_manage_co_owners` | Boolean (computed) | Whether current user can manage co-owners |
| `co_owner_count` | Integer (computed) | Total number of co-owners |
| `is_owned_by_me` | Boolean (computed) | Whether current user owns or co-owns record |

#### Methods

##### `transfer_ownership(new_owner_id, reason=None)`
Transfer ownership to a new user.

**Parameters:**
- `new_owner_id` (int): ID of the new owner
- `reason` (str, optional): Reason for transfer

**Returns:** `bool` - True if successful

**Raises:**
- `AccessError`: If user cannot transfer ownership
- `ValidationError`: If new owner is invalid

**Example:**
```python
record.transfer_ownership(new_owner.id, reason="Project handover")
```

##### `release_ownership(reason=None)`
Release current ownership.

**Parameters:**
- `reason` (str, optional): Reason for release

**Returns:** `bool` - True if successful

##### `claim_ownership(reason=None)`
Claim ownership of an unowned record.

**Parameters:**
- `reason` (str, optional): Reason for claiming

**Returns:** `bool` - True if successful

##### `add_co_owner(user_id, reason=None)`
Add a co-owner to the record.

**Parameters:**
- `user_id` (int): ID of user to add as co-owner
- `reason` (str, optional): Reason for addition

**Returns:** `bool` - True if successful

##### `remove_co_owner(user_id, reason=None)`
Remove a co-owner from the record.

**Parameters:**
- `user_id` (int): ID of user to remove
- `reason` (str, optional): Reason for removal

**Returns:** `bool` - True if successful

##### `add_multiple_co_owners(user_ids, reason=None)`
Add multiple co-owners to the record.

**Parameters:**
- `user_ids` (list): List of user IDs to add
- `reason` (str, optional): Reason for addition

**Returns:** `bool` - True if successful

##### `is_owner_or_co_owner(user=None)`
Check if a user is the owner or a co-owner.

**Parameters:**
- `user` (res.users, optional): User to check (defaults to current user)

**Returns:** `bool` - True if user is owner or co-owner

##### `get_all_owners()`
Get all owners (owner + co-owners) as a recordset.

**Returns:** `res.users` recordset

#### Search Methods

##### `_search_is_owned(operator, value)`
Search for owned/unowned records.

##### `_search_can_transfer(operator, value)`
Search for records current user can transfer.

##### `_search_is_owned_by_me(operator, value)`
Search for records owned by current user.

---

### `tk.assignable.mixin`

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `assigned_user_ids` | Many2many('res.users') | Users assigned to this record |
| `assigner_id` | Many2one('res.users') | User who made the assignment |
| `assignment_date` | Datetime | When assignment was made |
| `assignment_deadline` | Datetime | Deadline for assignment |
| `assignment_status` | Selection | Status of assignment |
| `assignment_priority` | Selection | Priority level |
| `assignment_description` | Text | Description of assignment |
| `is_assigned` | Boolean (computed) | Whether record is assigned |
| `is_overdue` | Boolean (computed) | Whether assignment is overdue |
| `can_assign` | Boolean (computed) | Whether current user can assign |
| `assigned_user_count` | Integer (computed) | Number of assigned users |
| `is_assigned_to_me` | Boolean (computed) | Whether current user is assigned |

#### Assignment Status Values
- `unassigned` - Not assigned to anyone
- `assigned` - Assigned but not started
- `in_progress` - Work in progress
- `completed` - Assignment completed
- `cancelled` - Assignment cancelled

#### Priority Values
- `low` - Low priority
- `normal` - Normal priority  
- `high` - High priority
- `urgent` - Urgent priority

#### Methods

##### `assign_to_users(user_ids, deadline=None, description=None, priority='normal', reason=None)`
Assign record to multiple users.

**Parameters:**
- `user_ids` (list): List of user IDs to assign to
- `deadline` (datetime, optional): Assignment deadline
- `description` (str, optional): Assignment description
- `priority` (str, optional): Assignment priority
- `reason` (str, optional): Reason for assignment

**Returns:** `bool` - True if successful

##### `add_assignee(user_id, reason=None)`
Add a user to the assignment.

**Parameters:**
- `user_id` (int): ID of user to assign
- `reason` (str, optional): Reason for assignment

**Returns:** `bool` - True if successful

##### `remove_assignee(user_id, reason=None)`
Remove a user from the assignment.

**Parameters:**
- `user_id` (int): ID of user to remove
- `reason` (str, optional): Reason for removal

**Returns:** `bool` - True if successful

##### `reassign_to_users(user_ids, reason=None)`
Reassign record to different users.

**Parameters:**
- `user_ids` (list): List of new user IDs
- `reason` (str, optional): Reason for reassignment

**Returns:** `bool` - True if successful

##### `unassign_all(reason=None)`
Remove all assignments from the record.

**Parameters:**
- `reason` (str, optional): Reason for unassignment

**Returns:** `bool` - True if successful

##### `start_assignment(reason=None)`
Mark assignment as in progress.

**Parameters:**
- `reason` (str, optional): Reason for starting

**Returns:** `bool` - True if successful

##### `complete_assignment(reason=None)`
Mark assignment as completed.

**Parameters:**
- `reason` (str, optional): Reason for completion

**Returns:** `bool` - True if successful

##### `cancel_assignment(reason=None)`
Cancel the assignment.

**Parameters:**
- `reason` (str, optional): Reason for cancellation

**Returns:** `bool` - True if successful

---

### `tk.accessible.mixin`

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `access_level` | Selection | Access level for the record |
| `allowed_user_ids` | Many2many('res.users') | Users with explicit access |
| `allowed_group_ids` | Many2many('res.groups') | Groups with access |
| `custom_access_group_ids` | Many2many('tk.accessible.group') | Custom access groups |
| `access_start_date` | Datetime | When access begins |
| `access_end_date` | Datetime | When access expires |
| `is_access_expired` | Boolean (computed) | Whether access has expired |
| `can_grant_access` | Boolean (computed) | Whether current user can grant access |
| `has_access` | Boolean (computed) | Whether current user has access |

#### Access Level Values
- `public` - Everyone can access
- `internal` - All internal users can access
- `restricted` - Only specified users/groups can access
- `private` - Only owner and specified users can access

#### Methods

##### `grant_access_to_user(user_id, start_date=None, end_date=None, reason=None)`
Grant access to a specific user.

**Parameters:**
- `user_id` (int): ID of user to grant access to
- `start_date` (datetime, optional): When access starts
- `end_date` (datetime, optional): When access expires
- `reason` (str, optional): Reason for granting access

**Returns:** `bool` - True if successful

##### `revoke_access_from_user(user_id, reason=None)`
Revoke access from a specific user.

**Parameters:**
- `user_id` (int): ID of user to revoke access from
- `reason` (str, optional): Reason for revocation

**Returns:** `bool` - True if successful

##### `_check_user_access(user)`
Check if a user has access to this record.

**Parameters:**
- `user` (res.users): User to check access for

**Returns:** `bool` - True if user has access

---

### `tk.responsible.mixin`

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `responsible_user_ids` | Many2many('res.users') | Primary responsible users |
| `secondary_responsible_ids` | Many2many('res.users') | Secondary responsible users |
| `responsibility_type` | Selection | Type of responsibility |
| `responsibility_start_date` | Datetime | When responsibility started |
| `responsibility_end_date` | Datetime | When responsibility ends |
| `responsibility_delegated_by` | Many2one('res.users') | Who delegated responsibility |
| `responsibility_description` | Text | Description of responsibility |
| `is_responsibility_active` | Boolean (computed) | Whether responsibility is active |
| `is_responsibility_expired` | Boolean (computed) | Whether responsibility expired |
| `can_delegate` | Boolean (computed) | Whether current user can delegate |
| `responsibility_count` | Integer (computed) | Number of responsible users |
| `secondary_responsibility_count` | Integer (computed) | Number of secondary responsible |

#### Responsibility Types
- `primary` - Primary responsibility
- `secondary` - Secondary responsibility
- `backup` - Backup responsibility
- `temporary` - Temporary responsibility

#### Methods

##### `assign_responsibility(user_ids, responsibility_type='primary', end_date=None, description=None, reason=None)`
Assign responsibility to users.

**Parameters:**
- `user_ids` (list): List of user IDs to assign responsibility to
- `responsibility_type` (str, optional): Type of responsibility
- `end_date` (datetime, optional): When responsibility ends
- `description` (str, optional): Description of responsibility
- `reason` (str, optional): Reason for assignment

**Returns:** `bool` - True if successful

##### `delegate_responsibility(user_ids, reason=None)`
Delegate responsibility to other users.

**Parameters:**
- `user_ids` (list): List of user IDs to delegate to
- `reason` (str, optional): Reason for delegation

**Returns:** `bool` - True if successful

##### `add_responsible_user(user_id, is_secondary=False, reason=None)`
Add a responsible user.

**Parameters:**
- `user_id` (int): ID of user to add
- `is_secondary` (bool, optional): Whether to add as secondary responsible
- `reason` (str, optional): Reason for addition

**Returns:** `bool` - True if successful

##### `remove_responsible_user(user_id, is_secondary=False, reason=None)`
Remove a responsible user.

**Parameters:**
- `user_id` (int): ID of user to remove
- `is_secondary` (bool, optional): Whether removing from secondary responsible
- `reason` (str, optional): Reason for removal

**Returns:** `bool` - True if successful

---

## Wizard Models API

### `tk.bulk.assign.wizard`

#### Fields
- `model_name` (Char): Target model name
- `record_ids` (Text): Record IDs to assign
- `user_ids` (Many2many): Users to assign to
- `assignment_deadline` (Datetime): Assignment deadline
- `assignment_priority` (Selection): Assignment priority
- `assignment_description` (Text): Assignment description
- `reason` (Text): Reason for assignment

#### Methods
##### `action_assign()`
Execute bulk assignment operation.

### `tk.transfer.ownership.wizard`

#### Fields
- `model_name` (Char): Target model name
- `record_id` (Integer): Record ID to transfer
- `current_owner_id` (Many2one): Current owner
- `new_owner_id` (Many2one): New owner
- `reason` (Text): Reason for transfer

#### Methods
##### `action_transfer()`
Execute ownership transfer.

### `tk.accessible.group.wizard`

#### Fields
- `name` (Char): Group name
- `description` (Text): Group description
- `group_type` (Selection): Type of group
- `access_level` (Selection): Group visibility
- `user_ids` (Many2many): Users in group
- `manager_ids` (Many2many): Group managers

#### Methods
##### `action_create_group()`
Create new access group.

##### `action_create_and_assign()`
Create group and assign to active records.

---

## Log Models API

### `tk.ownership.log`

#### Fields
- `model_name` (Char): Model of the record
- `res_id` (Integer): Record ID
- `action` (Selection): Type of action performed
- `old_owner_id` (Many2one): Previous owner
- `new_owner_id` (Many2one): New owner
- `reason` (Text): Reason for change
- `user_id` (Many2one): User who performed action
- `date` (Datetime): When action occurred

#### Action Types
- `transfer` - Ownership transferred
- `release` - Ownership released
- `claim` - Ownership claimed
- `add_co_owner` - Co-owner added
- `remove_co_owner` - Co-owner removed

### `tk.assignment.log`

#### Fields
- `model_name` (Char): Model of the record
- `res_id` (Integer): Record ID
- `action` (Selection): Type of action performed
- `old_assigned_user_id` (Many2one): Previous assignee
- `new_assigned_user_id` (Many2one): New assignee
- `reason` (Text): Reason for change
- `user_id` (Many2one): User who performed action
- `date` (Datetime): When action occurred

### `tk.access.log`

#### Fields
- `model_name` (Char): Model of the record
- `res_id` (Integer): Record ID
- `action` (Selection): Type of action performed
- `user_affected_id` (Many2one): User affected by change
- `old_access_level` (Selection): Previous access level
- `new_access_level` (Selection): New access level
- `reason` (Text): Reason for change
- `user_id` (Many2one): User who performed action
- `date` (Datetime): When action occurred

### `tk.responsibility.log`

#### Fields
- `model_name` (Char): Model of the record
- `res_id` (Integer): Record ID
- `action` (Selection): Type of action performed
- `old_responsible_user_id` (Many2one): Previous responsible user
- `new_responsible_user_id` (Many2one): New responsible user
- `reason` (Text): Reason for change
- `user_id` (Many2one): User who performed action
- `date` (Datetime): When action occurred

---

## Dashboard API

### `tk.comprehensive.dashboard`

#### Fields
- `date_from` (Date): Start date for statistics
- `date_to` (Date): End date for statistics
- `total_ownership_changes` (Integer): Total ownership changes in period
- `total_assignment_changes` (Integer): Total assignment changes in period
- `total_access_changes` (Integer): Total access changes in period
- `total_responsibility_changes` (Integer): Total responsibility changes in period
- `my_owned_records_count` (Integer): Records owned by current user
- `my_assignments_count` (Integer): Records assigned to current user
- `my_responsibilities_count` (Integer): Records user is responsible for

#### Methods
##### `action_refresh_dashboard()`
Refresh all dashboard statistics.

##### `get_ownable_models()`
Get list of models that inherit ownable mixin.

##### `get_assignable_models()`
Get list of models that inherit assignable mixin.

---

## Error Handling

### Exception Types

#### `AccessError`
Raised when user doesn't have permission to perform an action.

**Common scenarios:**
- Transferring ownership without permission
- Assigning users without assign rights
- Delegating responsibility without delegation rights

#### `ValidationError`
Raised when invalid data is provided.

**Common scenarios:**
- Invalid user IDs
- Invalid dates
- Conflicting assignments

### Error Messages

All error messages are translatable using Odoo's `_()` function. Common patterns:

```python
raise AccessError(_("You don't have permission to transfer ownership of this record."))
raise ValidationError(_("Invalid user specified for assignment."))
```

---

## Constants and Enumerations

### Selection Field Values

#### Access Levels
```python
ACCESS_LEVELS = [
    ('public', 'Public'),
    ('internal', 'Internal'),
    ('restricted', 'Restricted'),
    ('private', 'Private')
]
```

#### Assignment Status
```python
ASSIGNMENT_STATUS = [
    ('unassigned', 'Unassigned'),
    ('assigned', 'Assigned'),
    ('in_progress', 'In Progress'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled')
]
```

#### Assignment Priority
```python
ASSIGNMENT_PRIORITY = [
    ('low', 'Low'),
    ('normal', 'Normal'),
    ('high', 'High'),
    ('urgent', 'Urgent')
]
```

#### Responsibility Types
```python
RESPONSIBILITY_TYPES = [
    ('primary', 'Primary Responsibility'),
    ('secondary', 'Secondary Responsibility'),
    ('backup', 'Backup Responsibility'),
    ('temporary', 'Temporary Responsibility')
]
```

---

## XML-RPC / JSON-RPC Examples

### Using the API remotely

```python
import xmlrpc.client

# Connection
url = 'http://localhost:8069'
db = 'your_database'
username = 'your_username'
password = 'your_password'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Transfer ownership
models.execute_kw(db, uid, password, 'my.model', 'transfer_ownership', 
                  [record_id], {'new_owner_id': new_owner_id, 'reason': 'API transfer'})

# Assign users
models.execute_kw(db, uid, password, 'my.model', 'assign_to_users',
                  [record_id], {'user_ids': [user1_id, user2_id], 'reason': 'API assignment'})
```

---

*For implementation examples, see the [Examples Guide](examples.md) or check the developer guide for detailed usage patterns.*
