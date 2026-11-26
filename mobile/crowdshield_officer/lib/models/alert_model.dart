class AlertModel {
  const AlertModel({
    required this.windowId,
    required this.startFrame,
    required this.endFrame,
    required this.startTime,
    required this.endTime,
    required this.averagePeople,
    required this.maximumPeople,
    required this.crowdLoad,
    required this.movementLoad,
    required this.movementEventSignal,
    required this.spatialLoad,
    required this.growthLoad,
    required this.persistenceLoad,
    required this.operationalRiskScore,
    required this.operationalRiskLevel,
    required this.dominantRiskFactor,
    required this.operationalRiskReason,
    required this.responseAction,
    required this.responsePriority,
    required this.responseReason,
    required this.activeSignals,
    required this.humanReviewRequired,
    required this.autonomousEmergencyAction,
  });

  final int windowId;
  final int startFrame;
  final int endFrame;

  final double startTime;
  final double endTime;

  final double averagePeople;
  final int maximumPeople;

  final double crowdLoad;
  final double movementLoad;
  final double movementEventSignal;
  final double spatialLoad;
  final double growthLoad;
  final double persistenceLoad;

  final double operationalRiskScore;
  final String operationalRiskLevel;
  final String dominantRiskFactor;
  final String operationalRiskReason;

  final String responseAction;
  final String responsePriority;
  final String responseReason;
  final String activeSignals;

  final bool humanReviewRequired;
  final bool autonomousEmergencyAction;

  factory AlertModel.fromJson(Map<String, dynamic> json) {
    return AlertModel(
      windowId: _toInt(json['window_id']),
      startFrame: _toInt(json['start_frame']),
      endFrame: _toInt(json['end_frame']),
      startTime: _toDouble(json['start_time']),
      endTime: _toDouble(json['end_time']),
      averagePeople: _toDouble(json['average_people']),
      maximumPeople: _toInt(json['maximum_people']),
      crowdLoad: _toDouble(json['crowd_load']),
      movementLoad: _toDouble(json['movement_load']),
      movementEventSignal:
          _toDouble(json['movement_event_signal']),
      spatialLoad: _toDouble(json['spatial_load']),
      growthLoad: _toDouble(json['growth_load']),
      persistenceLoad: _toDouble(json['persistence_load']),
      operationalRiskScore:
          _toDouble(json['operational_risk_score']),
      operationalRiskLevel:
          json['operational_risk_level']?.toString() ?? 'UNKNOWN',
      dominantRiskFactor:
          json['dominant_risk_factor']?.toString() ?? '',
      operationalRiskReason:
          json['operational_risk_reason']?.toString() ?? '',
      responseAction:
          json['response_action']?.toString() ?? 'UNKNOWN',
      responsePriority:
          json['response_priority']?.toString() ?? 'UNKNOWN',
      responseReason:
          json['response_reason']?.toString() ?? '',
      activeSignals:
          json['active_signals']?.toString() ?? '',
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