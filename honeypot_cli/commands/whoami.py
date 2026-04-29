def run(args, current_directory, context=None):
    return (context or {}).get("username", "guest")
