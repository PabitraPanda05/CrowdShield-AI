class RiskModel {
  const RiskModel({
    required this.windowId,
    required this.startTime,
    required this.endTime,
    required this.operationalRiskScore,
    required this.operationalRiskLevel,
    required this.dominantRiskFactor,
    required this.operationalRiskReason,
  });

  final int windowId;

  final double startTime;
  final double endTime;

  final double operationalRiskScore;

  final String operationalRiskLevel;

  final String dominantRiskFactor;

  final String operationalRiskReason;

  factory RiskModel.fromJson(Map<String, dynamic> json) {
    return RiskModel(
      windowId: _toInt(json['window_id']),
      startTime: _toDouble(json['start_time']),
      endTime: _toDouble(json['end_time']),
      operationalRiskScore:
          _toDouble(json['operational_risk_score']),
      operationalRiskLevel:
          json['operational_risk_level']?.toString() ??
              'UNKNOWN',
      dominantRiskFactor:
          json['dominant_risk_factor']?.toString() ??
              'unknown',
      operationalRiskReason:
          json['operational_risk_reason']?.toString() ??
              '',
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