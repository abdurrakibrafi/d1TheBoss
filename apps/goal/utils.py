# apps/goals/utils.py

def get_user_primary_goal_type(user):
    """
    Determine user's primary goal based on their faith goal selections
    Returns: 'scripture', 'conversation', or 'share_faith'
    """
    from apps.onboarding.models import FaithGoal  
    
    # Get user's faith goal selections
    user_goals = FaithGoal.objects.filter(user=user)
    
    if not user_goals.exists():
        return 'scripture'  # Default goal
    
    # Count goal types based on selected options
    confidence_count = 0
    scripture_count = 0
    inspiration_count = 0
    
    for goal in user_goals:
        if goal.faith_goal_option and goal.faith_goal_option.option:
            option_text = goal.faith_goal_option.option.lower()
            
            # Check which category this option belongs to
            if any(keyword in option_text for keyword in ['confidence', 'respond', 'speak about faith', 'equipped', 'clarity', 'objections']):
                confidence_count += 1
            elif any(keyword in option_text for keyword in ['scripture', 'understanding', 'word', 'guidance', 'apply', 'insights']):
                scripture_count += 1
            elif any(keyword in option_text for keyword in ['inspire', 'encourage', 'share', 'others', 'journey']):
                inspiration_count += 1
    
    # Return the goal type with highest count
    if confidence_count >= scripture_count and confidence_count >= inspiration_count:
        return 'conversation'  # Maps to confidence goal
    elif inspiration_count >= scripture_count:
        return 'share_faith'   # Maps to inspiration goal
    else:
        return 'scripture'     # Maps to scripture knowledge goal