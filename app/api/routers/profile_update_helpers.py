"""
Profile update helpers for user router.

This module provides helper functions to parse and validate form data
for the user profile update endpoint, making the main route handler cleaner.
"""

import json
import re
from typing import Any, Dict, Optional
from pydantic import ValidationError
from app.schemas.cv_extraction import WorkExperience, Education, Certification
from app.schemas.user import JobPreferencesUpdate


def parse_json_field(field_str: Optional[str], field_name: str) -> Any:
    """
    Parse a JSON string field from form data.

    Args:
        field_str: The JSON string from form data (or None if not provided)
        field_name: Name of the field for error messages

    Returns:
        Parsed JSON data or None if field_str is None

    Raises:
        ValueError: If JSON parsing fails
    """
    if field_str is None:
        return None

    try:
        return json.loads(field_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"{field_name}: Invalid JSON format - {str(e)}")


def validate_array_field(data: Any, field_name: str) -> list:
    """
    Validate that data is a list/array.

    Args:
        data: The data to validate
        field_name: Name of the field for error messages

    Returns:
        The data as a list

    Raises:
        ValueError: If data is not a list
    """
    if not isinstance(data, list):
        raise ValueError(f"{field_name}: Must be a list/array")
    return data


def validate_experience_item(item: Dict, index: int) -> None:
    """
    Validate a single experience item using Pydantic schema.

    Args:
        item: The experience item dict
        index: Index for error messages

    Raises:
        ValueError: If validation fails
    """
    try:
        WorkExperience(**item)
    except ValidationError as e:
        error = e.errors()[0]
        field = error["loc"][0] if error["loc"] else "field"
        raise ValueError(f"Experience[{index}].{field}: {error['msg']}")


def validate_education_item(item: Dict, index: int) -> None:
    """
    Validate a single education item using Pydantic schema.

    Args:
        item: The education item dict
        index: Index for error messages

    Raises:
        ValueError: If validation fails
    """
    try:
        Education(**item)
    except ValidationError as e:
        error = e.errors()[0]
        field = error["loc"][0] if error["loc"] else "field"
        raise ValueError(f"Education[{index}].{field}: {error['msg']}")


def validate_certification_item(item: Dict, index: int) -> None:
    """
    Validate a single certification item using Pydantic schema.

    Args:
        item: The certification item dict
        index: Index for error messages

    Raises:
        ValueError: If validation fails
    """
    try:
        Certification(**item)
    except ValidationError as e:
        error = e.errors()[0]
        field = error["loc"][0] if error["loc"] else "field"
        raise ValueError(f"Certification[{index}].{field}: {error['msg']}")


def parse_experience(experience_str: Optional[str]) -> Optional[list]:
    """
    Parse and validate experience data from form field.

    Args:
        experience_str: JSON string of experience array

    Returns:
        List of validated experience items or None
    """
    data = parse_json_field(experience_str, "experience")
    if data is None:
        return None

    items = validate_array_field(data, "experience")
    for i, item in enumerate(items):
        validate_experience_item(item, i)

    return items


def parse_education(education_str: Optional[str]) -> Optional[list]:
    """
    Parse and validate education data from form field.

    Args:
        education_str: JSON string of education array

    Returns:
        List of validated education items or None
    """
    data = parse_json_field(education_str, "education")
    if data is None:
        return None

    items = validate_array_field(data, "education")
    for i, item in enumerate(items):
        validate_education_item(item, i)

    return items


def parse_certifications(certifications_str: Optional[str]) -> Optional[list]:
    """
    Parse and validate certifications data from form field.

    Args:
        certifications_str: JSON string of certifications array

    Returns:
        List of validated certification items or None
    """
    data = parse_json_field(certifications_str, "certifications")
    if data is None:
        return None

    items = validate_array_field(data, "certifications")
    for i, item in enumerate(items):
        validate_certification_item(item, i)

    return items


def parse_skills(skills_str: Optional[str]) -> Optional[list]:
    """
    Parse skills array from form field.

    Args:
        skills_str: JSON string of skills array

    Returns:
        List of skills or None
    """
    data = parse_json_field(skills_str, "skills")
    if data is None:
        return None
    return validate_array_field(data, "skills")


def parse_languages(languages_str: Optional[str]) -> Optional[list]:
    """
    Parse languages array from form field.

    Args:
        languages_str: JSON string of languages array

    Returns:
        List of languages or None
    """
    data = parse_json_field(languages_str, "languages")
    if data is None:
        return None
    return validate_array_field(data, "languages")


def parse_profile_data(
    summary: Optional[str], email: Optional[str]
) -> Optional[Dict[str, str]]:
    """
    Build profile data dict from summary and email fields.

    Args:
        summary: Profile summary text
        email: Email address

    Returns:
        Profile data dict or None if both are None
    """
    profile_data = {}

    if email is not None:
        profile_data["email"] = email
    if summary is not None:
        profile_data["summary"] = summary

    return profile_data if profile_data else None


def parse_salary(salary_str: Optional[str], field_name: str) -> Optional[float]:
    """
    Parse salary amount from string.

    Args:
        salary_str: String representation of salary
        field_name: Field name for error messages

    Returns:
        Salary as float or None

    Raises:
        ValueError: If parsing fails
    """
    if salary_str is None:
        return None

    try:
        return float(salary_str)
    except ValueError:
        raise ValueError(f"{field_name}: Must be a valid number")


def parse_string_array(array_str: Optional[str], field_name: str) -> Optional[list]:
    """
    Parse array of strings from JSON.

    Args:
        array_str: JSON string of array
        field_name: Field name for error messages

    Returns:
        List of strings or None
    """
    data = parse_json_field(array_str, field_name)
    if data is None:
        return None
    return validate_array_field(data, field_name)


def parse_boolean(bool_str: Optional[str]) -> Optional[bool]:
    """
    Parse boolean from string value.

    Args:
        bool_str: String representation ("true", "false", "1", "0", "yes", "no")

    Returns:
        Boolean value or None
    """
    if bool_str is None:
        return None

    return bool_str.lower() in ("true", "1", "yes")


def parse_job_preferences(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse all job preference fields from form data.

    Args:
        form_data: Dictionary of form fields

    Returns:
        Dictionary of parsed job preferences (only includes provided fields)
    """
    preferences = {}

    # Parse array fields
    locations = parse_string_array(
        form_data.get("preferred_locations"), "preferred_locations"
    )
    if locations is not None:
        preferences["preferred_locations"] = locations

    work_modes = parse_string_array(
        form_data.get("preferred_work_modes"), "preferred_work_modes"
    )
    if work_modes is not None:
        preferences["preferred_work_modes"] = work_modes

    job_types = parse_string_array(
        form_data.get("preferred_job_types"), "preferred_job_types"
    )
    if job_types is not None:
        preferences["preferred_job_types"] = job_types

    industries = parse_string_array(
        form_data.get("preferred_industries"), "preferred_industries"
    )
    if industries is not None:
        preferences["preferred_industries"] = industries

    divisions = parse_string_array(
        form_data.get("preferred_divisions"), "preferred_divisions"
    )
    if divisions is not None:
        preferences["preferred_divisions"] = divisions

    # Parse salary fields
    salary_min = parse_salary(
        form_data.get("expected_salary_min"), "expected_salary_min"
    )
    if salary_min is not None:
        preferences["expected_salary_min"] = salary_min

    salary_max = parse_salary(
        form_data.get("expected_salary_max"), "expected_salary_max"
    )
    if salary_max is not None:
        preferences["expected_salary_max"] = salary_max

    # Parse boolean field
    auto_apply = parse_boolean(form_data.get("auto_apply_enabled"))
    if auto_apply is not None:
        preferences["auto_apply_enabled"] = auto_apply

    return preferences


def parse_cv_data(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse all CV-related data from form data.

    Args:
        form_data: Dictionary of form fields

    Returns:
        Dictionary of parsed CV data (only includes provided fields)
    """
    cv_data = {}

    # Parse profile data (summary and email)
    profile = parse_profile_data(form_data.get("summary"), form_data.get("email"))
    if profile:
        cv_data["profile"] = profile

    # Parse arrays
    skills = parse_skills(form_data.get("skills"))
    if skills is not None:
        cv_data["skills"] = skills

    languages = parse_languages(form_data.get("languages"))
    if languages is not None:
        cv_data["languages"] = languages

    experience = parse_experience(form_data.get("experience"))
    if experience is not None:
        cv_data["experience"] = experience

    education = parse_education(form_data.get("education"))
    if education is not None:
        cv_data["education"] = education

    certifications = parse_certifications(form_data.get("certifications"))
    if certifications is not None:
        cv_data["certifications"] = certifications

    return cv_data


def validate_job_preferences(preferences: Dict[str, Any]) -> JobPreferencesUpdate:
    """
    Validate job preferences using Pydantic schema.

    Args:
        preferences: Dictionary of job preferences

    Returns:
        Validated JobPreferencesUpdate instance

    Raises:
        ValueError: If validation fails with formatted error message
    """
    try:
        return JobPreferencesUpdate(**preferences)
    except ValidationError as e:
        error = e.errors()[0]
        loc_parts = error["loc"] if error["loc"] else ["field"]
        error_msg = error.get("msg", "")

        # Build readable field name
        if (
            len(loc_parts) >= 2
            and isinstance(loc_parts[0], str)
            and isinstance(loc_parts[1], int)
        ):
            # This is an array item error (e.g., preferred_work_modes > 0)
            field_name = loc_parts[0].replace("_", " ").title()
            item_index = loc_parts[1] + 1  # Convert to 1-based index for users
            raise ValueError(f"{field_name} item #{item_index} {error_msg}")
        elif len(loc_parts) == 1:
            # Simple field error
            field_name = loc_parts[0].replace("_", " ").title()
            raise ValueError(f"{field_name}: {error_msg}")
        else:
            # Fallback for other error formats
            field_name = " > ".join(str(l) for l in loc_parts).replace("_", " ").title()
            raise ValueError(f"{field_name}: {error_msg}")


def get_first_error_message(error: Exception) -> str:
    """
    Extract the first error message from an exception.

    Args:
        error: The exception that occurred

    Returns:
        Formatted error message
    """
    if isinstance(error, ValueError):
        return str(error)
    return f"Validation failed: {str(error)}"
