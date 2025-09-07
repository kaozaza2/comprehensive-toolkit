# Comprehensive Toolkit for Odoo

A powerful Odoo module that provides comprehensive mixins and functionality for advanced record management including ownership, assignment, access control, and responsibility management.

## 🚀 Features

### Core Mixins

#### 1. **Ownable Mixin** (`tk.ownable.mixin`)
- **Owner Management**: Single owner with co-owner support
- **Ownership Transfer**: Transfer ownership between users with logging
- **Ownership Release**: Release ownership to make records unowned
- **Ownership Claiming**: Claim ownership of unowned records
- **Co-owner Management**: Add/remove multiple co-owners
- **Computed Fields**: `is_owned`, `can_transfer`, `can_release`, `is_owned_by_me`

#### 2. **Assignable Mixin** (`tk.assignable.mixin`)
- **Multi-user Assignment**: Assign records to multiple users
- **Assignment Status Tracking**: Unassigned, Assigned, In Progress, Completed, Cancelled
- **Priority Management**: Low, Normal, High, Urgent priority levels
- **Deadline Management**: Assignment deadlines with overdue detection
- **Assignment Description**: Detailed task descriptions
- **Smart Permissions**: Context-aware assignment permissions

#### 3. **Accessible Mixin** (`tk.accessible.mixin`)
- **Access Levels**: Public, Internal, Restricted, Private
- **User-based Access**: Direct user access permissions
- **Group-based Access**: Odoo group access permissions
- **Custom Access Groups**: Create custom access groups with the `tk.accessible.group` model
- **Time-based Access**: Access start and end dates
- **Computed Access**: Real-time access permission calculation

#### 4. **Responsible Mixin** (`tk.responsible.mixin`)
- **Primary & Secondary Responsibility**: Multiple responsibility levels
- **Responsibility Types**: Primary, Secondary, Backup, Temporary
- **Time-bound Responsibility**: Start and end dates for temporary responsibilities
- **Delegation Support**: Track who delegated responsibilities
- **Responsibility Descriptions**: Detailed responsibility documentation

### Advanced Features

#### 🏠 **Custom Access Groups** (`tk.accessible.group`)
- Create reusable access groups with custom names and descriptions
- Manage group membership independently of Odoo groups
- Apply access groups across multiple records efficiently

#### 📊 **Comprehensive Dashboard**
- Real-time statistics for all mixin activities
- User-specific counters (my assignments, responsibilities, etc.)
- Recent activity tracking
- Date-filtered reporting
- Overdue and expired item detection

#### 📝 **Complete Audit Logging**
- **Ownership Log**: Track all ownership changes with reasons
- **Assignment Log**: Monitor assignment activities
- **Access Log**: Log access permission changes
- **Responsibility Log**: Track responsibility delegation and changes

#### 🧙‍♂️ **Bulk Operation Wizards**
- **Accessible Group Wizard**: Manage group memberships efficiently
- **Bulk Operations**: Mass assignment, ownership transfer, and access management

## 🛠️ Installation

1. Copy the module to your Odoo addons directory
2. Update the apps list: `odoo -u all -d your_database`
3. Install the module from Apps menu

### Dependencies
- `base` (Odoo core)
- `web` (Web interface)

## 📚 Quick Start

### Basic Usage

```python
# Example: Project Task model using all mixins
class ProjectTask(models.Model):
    _name = 'your.project.task'
    _inherit = [
        'tk.ownable.mixin',           # Ownership functionality
        'tk.assignable.mixin',        # Assignment functionality  
        'tk.accessible.mixin',        # Access control
        'tk.responsible.mixin'        # Responsibility management
    ]
    
    name = fields.Char('Task Name', required=True)
    description = fields.Text('Description')
```

### Ownership Management
```python
# Transfer ownership
task.transfer_ownership(new_user.id, reason="Project handover")

# Add co-owners
task.add_co_owner(user.id, reason="Collaboration needed")

# Release ownership
task.release_ownership(reason="Task completed")

# Check ownership
is_owned = task.is_owned_by_me # or task.is_owner_or_co_owner(user.id)
```

### Assignment Management
```python
# Assign to multiple users
task.assign_to_users(
    [user1.id, user2.id], 
    deadline=fields.Datetime.now() + timedelta(days=7),
    description="Complete feature implementation",
    priority='high'
)

# Change assignment status
task.assignment_status = 'in_progress'

# Check if assigned
assigned = task.is_assigned_to_me # or task.is_assigned_to_user(user.id)
```

### Access Control
```python
# Set access level
task.set_access_level(
    'restricted', 
    reason="Confidential project"
)

# Set time-based access
task.set_access_duration(
    start_date=fields.Datetime.now(),
    end_date=fields.Datetime.now() + timedelta(days=30),
    reason="Temporary access for review"
)

# Grant access to specific user
task.grant_access_to_user(
    user_id=user1.id,
    start_date=optional_start_date,
    end_date=optional_end_date,
    reason="Need review access",
)

# Create custom access group
task.create_and_assign_custom_group(
    group_name="Project Alpha Team",
    user_ids=[user1.id, user2.id, user3.id],
    group_type="custom", # project, department, temporary, custom
    reason="Project team access"
)

# Check access
has_access = task._check_user_access(user.id)
```

### Responsibility Management
```python
# Assign responsibility
task.assign_responsibility(
    [user1.id],
    description="Overall project coordination"
)

# Delegate responsibility
task.delegate_responsibility(
    user2.id, 
    end_date=fields.Datetime.now() + timedelta(days=30),
    reason="Temporary delegation during vacation"
)
```

## 🎯 Use Cases

- **Project Management**: Task ownership, assignment, and responsibility tracking
- **Document Management**: Access control and ownership for documents
- **Customer Relationship Management**: Assign accounts to teams with proper access control
- **Asset Management**: Track asset ownership and responsibility
- **Workflow Management**: Complex approval and assignment workflows

## 🔧 Configuration

### Security Groups
The module creates several security groups:
- **Toolkit Manager**: Full access to all toolkit features
- **Toolkit User**: Basic access to use toolkit features
- **Toolkit Viewer**: Read-only access to toolkit data

### Menu Structure
- **Comprehensive Toolkit**
  - **Dashboard**: Overview and statistics
  - **Logs**: Audit trails for all activities
    - Ownership Logs
    - Assignment Logs  
    - Access Logs
    - Responsibility Logs
  - **Access Groups**: Manage custom access groups
  - **Configuration**: Settings and bulk operations

## 📈 Dashboard Features

Access the comprehensive dashboard to monitor:
- Total activity statistics across all mixins
- User-specific counters (owned, assigned, responsible)
- Recent activity summaries
- Overdue assignments and expired responsibilities
- Date-filtered reporting

## 🔍 Advanced Features

### Smart Permission System
The mixins include intelligent permission checking that considers:
- Current user context
- Record ownership (including co-owners)
- Access levels and restrictions
- Assignment status
- Group memberships

### Audit Trail
Complete logging system tracks:
- Who performed actions
- When actions occurred
- Reasons for changes
- Old and new values
- Full change history

### Bulk Operations
Efficient wizards for:
- Mass ownership transfers
- Bulk assignment operations
- Group membership management
- Access permission updates

## 📖 Documentation

- [Installation Guide](docs/installation.md)
- [User Guide](docs/user-guide.md)
- [Developer Guide](docs/developer-guide.md)
- [API Reference](docs/api-reference.md)
- [Examples](docs/examples.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🤝 Contributing

This project is developed by MokiMikore. Contributions, issues, and feature requests are welcome!

## 📄 License

This project is licensed under LGPL-3 - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **GitHub**: [https://github.com/kaozaza2](https://github.com/kaozaza2)
- **Author**: MokiMikore

---

**Compatible with Odoo 16.0+**
