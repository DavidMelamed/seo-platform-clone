deploy_target = "railway"
deploy_config = {
  start_command = "nixpacks start"
  health_check_path = "/health"
  restart_policy = "always"
}
