class ApiConfig {
  ApiConfig._();

  static const String baseUrl = 'http://172.28.36.162:8000';

  static const Duration requestTimeout = Duration(seconds: 10);

  static const String healthEndpoint = '/api/health';

  static const String dashboardSummaryEndpoint = '/api/dashboard/summary';

  static const String riskTimelineEndpoint = '/api/risk/timeline';

  static const String alertsEndpoint = '/api/alerts';

  static const String camerasEndpoint = '/api/cameras';
  static String cameraIntelligenceEndpoint(String cameraId) =>
      '/api/cameras/${Uri.encodeComponent(cameraId)}/intelligence';

  static const String crowdIntelligenceEndpoint = '/api/crowd-intelligence';

  static const String crowdAlertsEndpoint = '/api/crowd-intelligence/alerts';

  static const String crowdFlowEndpoint = '/api/crowd-intelligence/flow';

  static const String simulatedRouteEndpoint = '/api/routes/simulated';

  static const String routeValidationEndpoint = '/api/routes/validation';

  static const String databaseHealthEndpoint = '/api/database/health';
}
