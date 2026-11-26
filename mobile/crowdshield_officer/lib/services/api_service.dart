import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/alert_model.dart';
import '../models/risk_model.dart';
import 'api_config.dart';

class ApiService {
  ApiService({http.Client? client}) : _client = client ?? http.Client();

  final http.Client _client;

  Uri _buildUri(String endpoint) {
    return Uri.parse('${ApiConfig.baseUrl}$endpoint');
  }

  Future<Map<String, dynamic>> getHealth() async {
    return _get(ApiConfig.healthEndpoint);
  }

  Future<Map<String, dynamic>> getDashboardSummary() async {
    return _get(ApiConfig.dashboardSummaryEndpoint);
  }

  Future<List<RiskModel>> getRiskTimeline() async {
    final response = await _get(ApiConfig.riskTimelineEndpoint);

    final data = response['data'];

    if (data is! List) {
      return [];
    }

    return data
        .whereType<Map>()
        .map((item) => RiskModel.fromJson(Map<String, dynamic>.from(item)))
        .toList();
  }

  Future<List<AlertModel>> getAlerts() async {
    final response = await _get(ApiConfig.alertsEndpoint);

    final data = response['alerts'];

    if (data is! List) {
      return [];
    }

    return data
        .whereType<Map>()
        .map((item) => AlertModel.fromJson(Map<String, dynamic>.from(item)))
        .toList();
  }

  Future<Map<String, dynamic>> getCameras() async {
    return _get(ApiConfig.camerasEndpoint);
  }

  Future<Map<String, dynamic>> getCameraIntelligence(String cameraId) async {
    return _get(ApiConfig.cameraIntelligenceEndpoint(cameraId));
  }

  Future<Map<String, dynamic>> getCrowdIntelligence() async {
    return _get(ApiConfig.crowdIntelligenceEndpoint);
  }

  Future<List<dynamic>> getCrowdAlerts() async {
    final response = await _get(ApiConfig.crowdAlertsEndpoint);

    final data = response['data'];

    return data is List ? data : [];
  }

  Future<List<dynamic>> getCrowdFlow() async {
    final response = await _get(ApiConfig.crowdFlowEndpoint);

    final data = response['data'];

    return data is List ? data : [];
  }

  Future<Map<String, dynamic>> getSimulatedRoute() async {
    return _get(ApiConfig.simulatedRouteEndpoint);
  }

  Future<Map<String, dynamic>> getRouteValidation() async {
    return _get(ApiConfig.routeValidationEndpoint);
  }

  Future<Map<String, dynamic>> getDatabaseHealth() async {
    return _get(ApiConfig.databaseHealthEndpoint);
  }

  Future<Map<String, dynamic>> _get(String endpoint) async {
    final uri = _buildUri(endpoint);

    try {
      final response = await _client.get(uri).timeout(ApiConfig.requestTimeout);

      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw ApiException(
          'API request failed',
          statusCode: response.statusCode,
          body: response.body,
        );
      }

      final decoded = jsonDecode(response.body);

      if (decoded is Map<String, dynamic>) {
        return decoded;
      }

      throw const ApiException('Unexpected API response format');
    } catch (error) {
      if (error is ApiException) {
        rethrow;
      }

      throw ApiException('Unable to connect to CrowdShield backend: $error');
    }
  }

  void dispose() {
    _client.close();
  }
}

class ApiException implements Exception {
  final String message;
  final int? statusCode;
  final String? body;

  const ApiException(this.message, {this.statusCode, this.body});

  @override
  String toString() {
    if (statusCode != null) {
      return 'ApiException($statusCode): $message';
    }

    return 'ApiException: $message';
  }
}
