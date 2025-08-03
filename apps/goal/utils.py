def get_user_primary_goal_type(user):
    """
    Determine user's primary goal based on:
    1. Direct goal preference (if set) - PRIORITY
    2. Faith goal selections (fallback)
    """
    from apps.onboarding.models import FaithGoal, UserGoalPreference
    
    # Check if user has direct goal preference first
    try:
        goal_preference = UserGoalPreference.objects.get(user=user)
        return goal_preference.goal_type
    except UserGoalPreference.DoesNotExist:
        pass
    
    # Fallback to faith goal calculation
    user_goals = FaithGoal.objects.filter(user=user)
    
    if not user_goals.exists():
        return 'scripture'  # Default goal
    
    # Your existing calculation logic...
    confidence_count = 0
    scripture_count = 0
    inspiration_count = 0
    
    for goal in user_goals:
        if goal.faith_goal_option and goal.faith_goal_option.option:
            option_text = goal.faith_goal_option.option.lower()
            
            if any(keyword in option_text for keyword in ['confidence', 'respond', 'speak about faith', 'equipped', 'clarity', 'objections']):
                confidence_count += 1
            elif any(keyword in option_text for keyword in ['scripture', 'understanding', 'word', 'guidance', 'apply', 'insights']):
                scripture_count += 1
            elif any(keyword in option_text for keyword in ['inspire', 'encourage', 'share', 'others', 'journey']):
                inspiration_count += 1
    
    if confidence_count >= scripture_count and confidence_count >= inspiration_count:
        return 'conversation'
    elif inspiration_count >= scripture_count:
        return 'share_faith'
    else:
        return 'scripture'