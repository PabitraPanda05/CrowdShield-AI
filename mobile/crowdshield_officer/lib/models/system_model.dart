class SystemHealthModel {
  const SystemHealthModel({
    required this.status,
    required this.service,
    required this.apiVersion,
    required this.pipelineSource,
    required this.humanReviewRequired,
    required this.autonomousEmergencyAction,
  });

  final String status;
  final String service;
  final String apiVersion;
  final String pipelineSource;
  final bool humanReviewRequired;
  final bool autonomousEmergencyAction;

  factory SystemHealthModel.fromJson(
    Map<String, dynamic> json,
  ) {
    return SystemHealthModel(
      status: json['status']?.toString() ?? 'UNKNOWN',
      service: json['service']?.toString() ?? 'UNKNOWN',
      apiVersion:
          json['api_version']?.toString() ?? 'UNKNOWN',
      pipelineSource:
          json['pipeline_source']?.toString() ?? 'UNKNOWN',
      humanReviewRequired:
          json['human_review_required'] == true,
      autonomousEmergencyAction:
          json['autonomous_emergency_action'] == true,
    );
  }
}

class DatabaseHealthModel {
  const DatabaseHealthModel({
    required this.database,
    required this.path,
    required this.integrity,
    required this.tables,
  });

  final String database;
  final String path;
  final String integrity;
  final List<String> tables;

  factory DatabaseHealthModel.fromJson(
    Map<String, dynamic> json,
  ) {
    final rawTables = json['tables'];

    return DatabaseHealthModel(
      database:
          json['database']?.toString() ?? 'UNKNOWN',
      path: json['path']?.toString() ?? '',
      integrity:
          json['integrity']?.toString() ?? 'UNKNOWN',
      tables: rawTables is List
          ? rawTables
              .map((item) => item.toString())
              .toList()
          : [],
    );
  }
}

class CameraModel {
  const CameraModel({
    required this.cameraId,
    required this.cameraName,
    required this.sourceFile,
    required this.status,
    required this.sourceType,
    required this.width,
    required this.height,
    required this.fps,
    required this.frameCount,
    required this.durationSeconds,
    required this.liveStream,
    required this.humanReviewRequired,
    required this.autonomousEmergencyAction,
  });

  final String cameraId;
  final String cameraName;
  final String sourceFile;
  final String status;
  final String sourceType;
  final int width;
  final int height;
  final double fps;
  final int frameCount;
  final double durationSeconds;
  final bool liveStream;
  final bool humanReviewRequired;
  final bool autonomousEmergencyAction;

  factory CameraModel.fromJson(
    Map<String, dynamic> json,
  ) {
    return CameraModel(
      cameraId:
          json['camera_id']?.toString() ?? 'UNKNOWN',
      cameraName:
          json['camera_name']?.toString() ?? 'UNKNOWN',
      sourceFile:
          json['source_file']?.toString() ?? '',
      status:
          json['status']?.toString() ?? 'UNKNOWN',
      sourceType:
          json['source_type']?.toString() ?? 'UNKNOWN',
      width: _toInt(json['width']),
      height: _toInt(json['height']),
      fps: _toDouble(json['fps']),
      frameCount: _toInt(json['frame_count']),
      durationSeconds:
          _toDouble(json['duration_sec']),
      liveStream:
          json['live_stream'] == true,
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

    return int.tryParse(
          value?.toString() ?? '',
        ) ??
        0;
  }

  static double _toDouble(dynamic value) {
    if (value is num) {
      return value.toDouble();
    }

    return double.tryParse(
          value?.toString() ?? '',
        ) ??
        0.0;
  }
}

class CameraResponseModel {
  const CameraResponseModel({
    required this.source,
    required this.cameraType,
    required this.cameraCount,
    required this.liveCameraAvailable,
    required this.humanReviewRequired,
    required this.autonomousEmergencyAction,
    required this.cameras,
  });

  final String source;
  final String cameraType;
  final int cameraCount;
  final bool liveCameraAvailable;
  final bool humanReviewRequired;
  final bool autonomousEmergencyAction;
  final List<CameraModel> cameras;

  factory CameraResponseModel.fromJson(
    Map<String, dynamic> json,
  ) {
    final rawData = json['data'];

    final cameras = rawData is List
        ? rawData
            .whereType<Map>()
            .map(
              (item) => CameraModel.fromJson(
                Map<String, dynamic>.from(item),
              ),
            )
            .toList()
        : <CameraModel>[];

    return CameraResponseModel(
      source:
          json['source']?.toString() ?? 'UNKNOWN',
      cameraType:
          json['camera_type']?.toString() ?? 'UNKNOWN',
      cameraCount:
          _toInt(json['camera_count']),
      liveCameraAvailable:
          json['live_camera_available'] == true,
      humanReviewRequired:
          json['human_review_required'] == true,
      autonomousEmergencyAction:
          json['autonomous_emergency_action'] == true,
      cameras: cameras,
    );
  }

  static int _toInt(dynamic value) {
    if (value is num) {
      return value.toInt();
    }

    return int.tryParse(
          value?.toString() ?? '',
        ) ??
        0;
  }
}