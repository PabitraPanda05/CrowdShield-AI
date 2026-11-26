class DashboardModel {
  const DashboardModel({
    required this.source,
    required this.summaryType,
    required this.riskInterpretation,
    required this.processedWindows,
    required this.minimumRiskScore,
    required this.meanRiskScore,
    required this.maximumRiskScore,
    required this.riskDistribution,
    required this.responseDistribution,
    required this.latestState,
    required this.humanReviewRequired,
    required this.autonomousEmergencyAction,
  });

  final String source;
  final String summaryType;
  final String riskInterpretation;

  final int processedWindows;

  final double minimumRiskScore;
  final double meanRiskScore;
  final double maximumRiskScore;

  final Map<String, int> riskDistribution;
  final Map<String, int> responseDistribution;

  final LatestRiskState latestState;

  final bool humanReviewRequired;
  final bool autonomousEmergencyAction;

  factory DashboardModel.fromJson(Map<String, dynamic> json) {
    return DashboardModel(
      source: json['source']?.toString() ?? '',
      summaryType: json['summary_type']?.toString() ?? '',
      riskInterpretation:
          json['risk_interpretation']?.toString() ?? '',
      processedWindows: _toInt(json['processed_windows']),
      minimumRiskScore: _toDouble(json['minimum_risk_score']),
      meanRiskScore: _toDouble(json['mean_risk_score']),
      maximumRiskScore: _toDouble(json['maximum_risk_score']),
      riskDistribution: _toIntMap(json['risk_distribution']),
      responseDistribution:
          _toIntMap(json['response_distribution']),
      latestState: LatestRiskState.fromJson(
        _toMap(json['latest_state']),
      ),
      humanReviewRequired:
          json['human_review_required'] == true,
      autonomousEmergencyAction:
          json['autonomous_emergency_action'] == true,
    );
  }

  static int _toInt(dynamic value) {
    if (value is num) {
      return value.toInt();
    }

    return int.tryParse(value?.toString() ?? '') ?? 0;
  }

  static double _toDouble(dynamic value) {
    if (value is num) {
      return value.toDouble();
    }

    return double.tryParse(value?.toString() ?? '') ?? 0.0;
  }

  static Map<String, int> _toIntMap(dynamic value) {
    if (value is! Map) {
      return {};
    }

    return value.map(
      (key, value) => MapEntry(
        key.toString(),
        _toInt(value),
      ),
    );
  }

  static Map<String, dynamic> _toMap(dynamic value) {
    if (value is Map<String, dynamic>) {
      return value;
    }

    if (value is Map) {
      return Map<String, dynamic>.from(value);
    }

    return {};
  }
}

class LatestRiskState {
  const LatestRiskState({
    required this.windowId,
    required this.riskScore,
    required this.riskLevel,
    required this.responseAction,
    required this.responsePriority,
    required this.humanReviewRequired,
    required this.autonomousEmergencyAction,
  });

  final int windowId;
  final double riskScore;
  final String riskLevel;
  final String responseAction;
  final String responsePriority;
  final bool humanReviewRequired;
  final bool autonomousEmergencyAction;

  factory LatestRiskState.fromJson(
    Map<String, dynamic> json,
  ) {
    return LatestRiskState(
      windowId: _toInt(json['window_id']),
      riskScore: _toDouble(json['risk_score']),
      riskLevel: json['risk_level']?.toString() ?? 'UNKNOWN',
      responseAction:
          json['response_action']?.toString() ?? 'UNKNOWN',
      responsePriority:
          json['response_priority']?.toString() ?? 'UNKNOWN',
      humanReviewRequired:
          json['human_review_required'] == true,
      autonomousEmergencyAction:
          json['autonomous_emergency_action'] == true,
    );
  }

  static int _toInt(dynamic value) {
    if (value is num) {
      return value.toInt();
    }

    return int.tryParse(value?.toString() ?? '') ?? 0;
  }

  static double _toDouble(dynamic value) {
    if (value is num) {
      return value.toDouble();
    }

    return double.tryParse(value?.toString() ?? '') ?? 0.0;
  }
}