# Changelog


## [1.0.2] - 2024-11-15

- Pass in Excel + word template
- Pass back word output

### Added
- Added 2nd Azure function for remediation formatting
- Added processing of Excel remediation spreadsheet to word doc
- Added OpenAI access

### Changed
- Extensive UI changes in MS Form. Removed several N/A options in radio selections (not in the codebase itself)
- Corrected rules logic to follow Tom's guidelines
- DB: dropped philips_form_submission.bp_5_2_justified
- DB: set override_quid = '' where rule_id = bp_5_2

## Removed
- Dropped requirement bp_5_2_justified

### Fixed
- philips_document_template.docx Section 10 subheader changed to: Verify correct operations of WLAN Controller and infrastructure support

## [1.0.1] - 2024-11-10

### Changed
- Changed formatting of sections (font, padding, background color)
- Replace 'Passed' with 'Meets Requirements'
- Removed 'Code'
- Moved Category back to it's own column
- Findings/Recommendations are shown after the progress bar, for only those things that fail
- Put each section on it's own page
- Added best practice titles, and subheadings

## [1.0.4] - 2024-11-20

### Changed
- Refactored scorecard generation code into a proper class structure
- Improved code organization and maintainability
- Separated scorecard generation logic from Azure Function entry point

### Technical Improvements
- Introduced new `ScorecardGenerator` class to encapsulate all scorecard building logic
- Improved database connection handling through class initialization
- Reduced code duplication in database access
- Better error handling and type hints
- Cleaner separation of concerns between modules
