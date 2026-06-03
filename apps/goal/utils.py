def get_user_primary_goal_type(user):
    print(f"=== GET_USER_PRIMARY_GOAL_TYPE DEBUG ===")
    print(f"User: {user.id}")
    
    from apps.onboarding.models import FaithGoal, UserGoalPreference
    try:
        goal_preference = UserGoalPreference.objects.get(user=user)
        print(f"Found goal preference: {goal_preference.goal_type}")
        return goal_preference.goal_type
    except UserGoalPreference.DoesNotExist:
        print("No goal preference found, calculating from faith goals")
    user_goals = FaithGoal.objects.filter(user=user).select_related('faith_goal_option')
    print(f"Found {user_goals.count()} faith goals")
    
    if not user_goals.exists():
        print("No faith goals found, returning default 'scripture'")
        return 'scripture'
    confidence_count = 0
    scripture_count = 0
    inspiration_count = 0
    
    for goal in user_goals:
        option = goal.faith_goal_option
        print(f"Processing goal - Option ID: {option.id}, Text: '{option.option}', Goal Type: '{option.goal_type}'")
        
        if option and option.goal_type:
            goal_type = option.goal_type
            
            if goal_type == 'conversation':
                confidence_count += 1
                print(f"  -> Added to confidence count")
            elif goal_type == 'scripture':
                scripture_count += 1
                print(f"  -> Added to scripture count")
            elif goal_type == 'share_faith':
                inspiration_count += 1
                print(f"  -> Added to inspiration count")
        else:
            print(f"  -> No goal_type found for this option!")
    
    print(f"Final counts - Confidence: {confidence_count}, Scripture: {scripture_count}, Inspiration: {inspiration_count}")
    if confidence_count > scripture_count and confidence_count > inspiration_count:
        result = 'conversation'
    elif inspiration_count > scripture_count and inspiration_count > confidence_count:
        result = 'share_faith'
    elif scripture_count > 0:
        result = 'scripture'
    else:
        result = 'scripture'  # Default
    
    print(f"Calculated goal type: {result}")
    return result