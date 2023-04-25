# Mist Plugin Changelog
## 0.7 (13/01/2023)
### Fixed
    Fixed a bug where switch config changes would not be reported correctly
        The 'new' config would be reported as the 'old' config
        
        
### Changed
    Moved the SQL table name into the config file, rather than hardcoding in the plugin


- - - -
## 0.6 (11/01/2023)
### Changed
    Changed the class to inherit from the plugin template class
      This simplifies the plugin

### Removed
    Removed the 'Mist Debug' module, as it wasn't really being used
      This info was already being logged to SQL
      This brings this plugin more in line with other plugins
      
