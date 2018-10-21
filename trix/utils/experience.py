from django.conf import settings
from trix.trix_core import models


def get_experience(assignments, user):
    """Gets the experience from the tags in the given assignments."""
    tags = []
    for assignment in assignments:
        tag_query = assignment.tags.filter(category='s')
        tags.append(list(tag_query))
    # Flatten list
    tags = [tag for sublist in tags for tag in sublist]
    tagexp = (models.TagExperience.objects
              .filter(user=user)
              .filter(tag__in=tags))
    exp = 0
    for tag in tagexp:
        exp += tag.experience
    return exp


def get_level(exp):
    """Calculates the level based on the given TagExperience objects."""
    level_caps = settings.LEVEL_CAPS
    for idx in reversed(range(len(level_caps))):
        if exp >= level_caps[idx]:
            return idx + 1


def current_level_exp(level):
    """Returns the experience required for the given level."""
    level_caps = settings.LEVEL_CAPS
    if level - 1 < 0:
        return level_caps[0]
    return level_caps[level - 1]


def next_level_exp(level):
    """Returns the experience required for the next level."""
    level_caps = settings.LEVEL_CAPS
    print(f"Level caps: {level_caps}\tlevel: {level}")
    if level >= len(level_caps) - 1:
        return level_caps[len(level_caps) - 1]
    elif level < 0:
        return level_caps[0]
    return level_caps[level]


def get_level_progress(xp, level):
    """Returns percentage progress towards next level as int at maximum 100."""
    base_lvl_xp = current_level_exp(level)
    next_lvl_xp = max(float(next_level_exp(level) - current_level_exp(level)), 1)  # max to avoid 0
    progress_lvl = xp - base_lvl_xp  # XP progress towards next level from current level
    percentage = round((progress_lvl / next_lvl_xp) * 100)  # Get the percentage and round it
    return min(int(percentage), 100)  # Return as it and at maximum 100 percent


def get_difficulty(assignments, user):
    """Returns the difficulty for the given level. Simply returns '2' on KeyError."""
    exp = get_experience(assignments, user)
    lvl = get_level(exp)
    cle = current_level_exp(lvl)
    try:
        difficulty = settings.DIFFICULTY_CAPS[cle]
    except KeyError as ke:
        difficulty = '2'  # highest difficulty
    finally:
        return difficulty
