import 'dart:async';

import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';
import '../../models/system_model.dart';
import '../../services/api_service.dart';

class CameraMonitoringScreen extends StatefulWidget {
  const CameraMonitoringScreen({super.key});

  @override
  State<CameraMonitoringScreen> createState() => _CameraMonitoringScreenState();
}

class _CameraMonitoringScreenState extends State<CameraMonitoringScreen> {
  final ApiService _apiService = ApiService();

  CameraResponseModel? cameraResponse;

  String? selectedCameraId;
  Map<String, dynamic>? cameraIntelligence;

  bool loading = true;
  bool intelligenceLoading = false;
  bool _intelligenceRequestInProgress = false;

  String? errorMessage;
  String? intelligenceError;

  Timer? _intelligenceTimer;

  @override
  void initState() {
    super.initState();
    _loadCameras();

    // Refresh selected-camera intelligence periodically.
    _intelligenceTimer = Timer.periodic(const Duration(seconds: 3), (_) {
      final cameraId = selectedCameraId;

      if (cameraId != null && !_intelligenceRequestInProgress) {
        _loadCameraIntelligence(cameraId, showLoading: false);
      }
    });
  }

  @override
  void dispose() {
    _intelligenceTimer?.cancel();
    _apiService.dispose();
    super.dispose();
  }

  Future<void> _loadCameras() async {
    if (!mounted) return;

    setState(() {
      loading = true;
      errorMessage = null;
    });

    try {
      final data = await _apiService.getCameras();
      final parsed = CameraResponseModel.fromJson(data);

      if (!mounted) return;

      final cameras = parsed.cameras;

      final currentExists = cameras.any(
        (camera) => camera.cameraId == selectedCameraId,
      );

      String? nextSelectedId = selectedCameraId;

      if (!currentExists) {
        final preferredCamera = cameras.where(
          (camera) =>
              camera.liveStream && camera.status.toUpperCase() == 'RUNNING',
        );

        nextSelectedId = preferredCamera.isNotEmpty
            ? preferredCamera.first.cameraId
            : cameras.isNotEmpty
            ? cameras.first.cameraId
            : null;
      }

      final selectionChanged = nextSelectedId != selectedCameraId;

      setState(() {
        cameraResponse = parsed;
        selectedCameraId = nextSelectedId;
        loading = false;

        if (selectionChanged) {
          cameraIntelligence = null;
          intelligenceError = null;
        }
      });

      if (nextSelectedId != null &&
          (selectionChanged || cameraIntelligence == null)) {
        await _loadCameraIntelligence(nextSelectedId, showLoading: true);
      }
    } catch (e) {
      if (!mounted) return;

      setState(() {
        loading = false;
        errorMessage = e.toString();
      });
    }
  }

  Future<void> _loadCameraIntelligence(
    String cameraId, {
    bool showLoading = true,
  }) async {
    if (!mounted || _intelligenceRequestInProgress) return;

    _intelligenceRequestInProgress = true;

    if (showLoading) {
      setState(() {
        intelligenceLoading = true;
        intelligenceError = null;
      });
    }

    try {
      final response = await _apiService.getCameraIntelligence(cameraId);

      if (!mounted || selectedCameraId != cameraId) return;

      final rawData = response['data'];

      setState(() {
        cameraIntelligence = rawData is Map
            ? Map<String, dynamic>.from(rawData)
            : null;

        intelligenceLoading = false;
        intelligenceError = null;
      });
    } catch (e) {
      if (!mounted || selectedCameraId != cameraId) return;

      setState(() {
        intelligenceLoading = false;
        intelligenceError = e.toString();
      });
    } finally {
      _intelligenceRequestInProgress = false;
    }
  }

  void _selectCamera(String cameraId) {
    if (selectedCameraId == cameraId) {
      _loadCameraIntelligence(cameraId, showLoading: true);
      return;
    }

    setState(() {
      selectedCameraId = cameraId;
      cameraIntelligence = null;
      intelligenceError = null;
      intelligenceLoading = true;
    });

    _loadCameraIntelligence(cameraId, showLoading: false);
  }

  @override
  Widget build(BuildContext context) {
    if (loading) {
      return const Center(
        child: CircularProgressIndicator(color: AppTheme.primaryColor),
      );
    }

    if (errorMessage != null) {
      return _buildError();
    }

    final response = cameraResponse;

    if (response == null || response.cameras.isEmpty) {
      return _buildEmpty();
    }

    final selectedCamera = response.cameras
        .where((camera) => camera.cameraId == selectedCameraId)
        .firstOrNull;

    return RefreshIndicator(
      color: AppTheme.primaryColor,
      backgroundColor: AppTheme.surfaceColor,
      onRefresh: _loadCameras,
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(16, 20, 16, 30),
        children: [
          _buildHeader(),
          const SizedBox(height: 22),

          _buildSourceOverview(),
          const SizedBox(height: 22),

          const _SectionHeader(
            title: 'Select Camera',
            icon: Icons.video_camera_back_outlined,
          ),
          const SizedBox(height: 12),

          _buildCameraSelector(response.cameras),
          const SizedBox(height: 22),

          const _SectionHeader(
            title: 'Camera Intelligence',
            icon: Icons.analytics_outlined,
          ),
          const SizedBox(height: 12),

          _buildIntelligencePanel(),
          const SizedBox(height: 22),

          const _SectionHeader(
            title: 'Available Cameras',
            icon: Icons.videocam_outlined,
          ),
          const SizedBox(height: 12),

          ...response.cameras.map(
            (camera) => Padding(
              padding: const EdgeInsets.only(bottom: 16),
              child: _CameraCard(
                camera: camera,
                selected: camera.cameraId == selectedCameraId,
                onTap: () => _selectCamera(camera.cameraId),
              ),
            ),
          ),

          const SizedBox(height: 8),
          _buildSafetyNotice(selectedCamera),
        ],
      ),
    );
  }

  // ============================================================
  // HEADER
  // ============================================================

  Widget _buildHeader() {
    final cameraCount = cameraResponse?.cameraCount ?? 0;
    return Row(
      children: [
        Container(
          width: 50,
          height: 50,
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [
                AppTheme.primaryColor.withValues(alpha: 0.22),
                AppTheme.primaryColor.withValues(alpha: 0.06),
              ],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: AppTheme.primaryColor.withValues(alpha: 0.30),
            ),
          ),
          child: const Icon(
            Icons.videocam_rounded,
            color: AppTheme.primaryColor,
            size: 26,
          ),
        ),
        const SizedBox(width: 13),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Camera Monitoring',
                style: TextStyle(
                  color: AppTheme.textPrimaryColor,
                  fontSize: 21,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -0.3,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                '$cameraCount configured camera${cameraCount == 1 ? '' : 's'}',
                style: const TextStyle(
                  color: AppTheme.textSecondaryColor,
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),
        Container(
          decoration: BoxDecoration(
            color: AppTheme.surfaceColor,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppTheme.borderColor),
          ),
          child: IconButton(
            onPressed: loading ? null : _loadCameras,
            tooltip: 'Refresh cameras',
            icon: const Icon(
              Icons.refresh_rounded,
              color: AppTheme.primaryColor,
            ),
          ),
        ),
      ],
    );
  }

  // ============================================================
  // SOURCE OVERVIEW
  // ============================================================

  Widget _buildSourceOverview() {
    final response = cameraResponse!;
    final isLive = response.liveCameraAvailable;
    final statusColor = isLive ? AppTheme.successColor : AppTheme.warningColor;

    return Container(
      padding: const EdgeInsets.all(17),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppTheme.surfaceColor,
            AppTheme.surfaceColor.withValues(alpha: 0.82),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: statusColor.withValues(alpha: 0.30)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  color: statusColor.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  isLive ? Icons.sensors_rounded : Icons.video_library_rounded,
                  color: statusColor,
                  size: 22,
                ),
              ),
              const SizedBox(width: 11),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'SOURCE OVERVIEW',
                      style: TextStyle(
                        color: AppTheme.textSecondaryColor,
                        fontSize: 10,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 1.0,
                      ),
                    ),
                    SizedBox(height: 3),
                    Text(
                      'Camera infrastructure',
                      style: TextStyle(
                        color: AppTheme.textPrimaryColor,
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ),
              ),
              _StatusBadge(
                text: isLive ? 'LIVE AVAILABLE' : response.cameraType,
                color: statusColor,
              ),
            ],
          ),
          const SizedBox(height: 17),
          Row(
            children: [
              Expanded(
                child: _MetricCard(
                  label: 'Total cameras',
                  value: response.cameraCount.toString(),
                  icon: Icons.videocam_outlined,
                  color: AppTheme.primaryColor,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _MetricCard(
                  label: 'Live availability',
                  value: isLive ? 'YES' : 'NO',
                  icon: isLive
                      ? Icons.wifi_tethering_rounded
                      : Icons.videocam_off_outlined,
                  color: statusColor,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          const Divider(color: AppTheme.borderColor, height: 1),
          const SizedBox(height: 14),
          _InfoRow(label: 'Configured source', value: response.source),
          const SizedBox(height: 10),
          _InfoRow(
            label: 'Camera mode',
            value: response.cameraType.replaceAll('_', ' '),
          ),
          const SizedBox(height: 10),
          _InfoRow(
            label: 'Human review',
            value: response.humanReviewRequired ? 'REQUIRED' : 'NOT REQUIRED',
          ),
          const SizedBox(height: 10),
          _InfoRow(
            label: 'Autonomous action',
            value: response.autonomousEmergencyAction ? 'ENABLED' : 'DISABLED',
          ),
        ],
      ),
    );
  }

  // ============================================================
  // CAMERA SELECTOR
  // ============================================================

  Widget _buildCameraSelector(List<CameraModel> cameras) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 5),
      decoration: BoxDecoration(
        color: AppTheme.surfaceColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppTheme.borderColor),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: cameras.any((camera) => camera.cameraId == selectedCameraId)
              ? selectedCameraId
              : null,
          isExpanded: true,
          dropdownColor: AppTheme.surfaceColor,
          hint: const Text('Choose a camera'),
          icon: const Icon(
            Icons.keyboard_arrow_down,
            color: AppTheme.primaryColor,
          ),
          items: cameras.map((camera) {
            return DropdownMenuItem<String>(
              value: camera.cameraId,
              child: Text(
                '${camera.cameraName} (${camera.cameraId})',
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: AppTheme.textPrimaryColor,
                  fontSize: 13,
                ),
              ),
            );
          }).toList(),
          onChanged: (cameraId) {
            if (cameraId != null) {
              _selectCamera(cameraId);
            }
          },
        ),
      ),
    );
  }

  // ============================================================
  // CAMERA INTELLIGENCE
  // ============================================================

  Widget _buildIntelligencePanel() {
    if (intelligenceLoading && cameraIntelligence == null) {
      return _panel(
        child: const Center(
          child: Padding(
            padding: EdgeInsets.all(22),
            child: CircularProgressIndicator(color: AppTheme.primaryColor),
          ),
        ),
      );
    }

    if (intelligenceError != null && cameraIntelligence == null) {
      return _panel(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Intelligence unavailable',
              style: TextStyle(
                color: AppTheme.textPrimaryColor,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              intelligenceError!,
              style: const TextStyle(
                color: AppTheme.textSecondaryColor,
                fontSize: 11,
              ),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: selectedCameraId == null
                  ? null
                  : () => _loadCameraIntelligence(selectedCameraId!),
              icon: const Icon(Icons.refresh),
              label: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    final data = cameraIntelligence;

    if (data == null) {
      return _panel(
        child: const Text(
          'Select a camera to view its latest intelligence.',
          style: TextStyle(color: AppTheme.textSecondaryColor, fontSize: 12),
        ),
      );
    }

    final latestFrame = _asMap(data['latest_frame']);
    final latestRisk = _asMap(data['latest_risk']);
    final latestResponse = _asMap(data['latest_response']);

    final personCount = _toInt(
      data['latest_person_count'] ?? latestFrame['person_count'],
    );

    final riskScore = _toDouble(latestRisk['operational_risk_score']);

    final riskLevel =
        latestRisk['operational_risk_level']?.toString() ?? 'UNKNOWN';

    final dominantFactor =
        latestRisk['dominant_risk_factor']?.toString() ?? 'unknown';

    final riskReason =
        latestRisk['operational_risk_reason']?.toString() ??
        'No risk explanation available.';

    final responseAction =
        latestResponse['response_action']?.toString() ?? 'UNKNOWN';

    final responsePriority =
        latestResponse['response_priority']?.toString() ?? 'UNKNOWN';

    final humanReviewRequired = latestResponse['human_review_required'] == true;

    final autonomousAction =
        latestResponse['autonomous_emergency_action'] == true;

    final riskColor = _riskColor(riskLevel);

    return _panel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      data['camera_name']?.toString() ??
                          selectedCameraId ??
                          'Selected Camera',
                      style: const TextStyle(
                        color: AppTheme.textPrimaryColor,
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${data['camera_id'] ?? ''} • '
                      '${data['source_type'] ?? 'UNKNOWN'}',
                      style: const TextStyle(
                        color: AppTheme.textSecondaryColor,
                        fontSize: 10,
                      ),
                    ),
                  ],
                ),
              ),
              _StatusBadge(
                text: data['status']?.toString() ?? 'UNKNOWN',
                color: _statusColor(data['status']?.toString() ?? ''),
              ),
            ],
          ),
          const SizedBox(height: 18),

          Row(
            children: [
              Expanded(
                child: _MetricCard(
                  label: 'People detected',
                  value: personCount.toString(),
                  icon: Icons.people_alt_outlined,
                  color: AppTheme.primaryColor,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _MetricCard(
                  label: 'Risk score',
                  value: riskScore.toStringAsFixed(1),
                  icon: Icons.shield_outlined,
                  color: riskColor,
                  footer: '/ 100',
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              const Expanded(
                child: Text(
                  'Risk score indicator',
                  style: TextStyle(
                    color: AppTheme.textSecondaryColor,
                    fontSize: 10,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              Text(
                '${riskScore.clamp(0.0, 100.0).toStringAsFixed(1)}%',
                style: TextStyle(
                  color: riskColor,
                  fontSize: 10,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ],
          ),
          const SizedBox(height: 7),
          ClipRRect(
            borderRadius: BorderRadius.circular(99),
            child: LinearProgressIndicator(
              value: riskScore.clamp(0.0, 100.0) / 100.0,
              minHeight: 7,
              backgroundColor: AppTheme.borderColor,
              valueColor: AlwaysStoppedAnimation<Color>(riskColor),
            ),
          ),
          const SizedBox(height: 15),

          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: riskColor.withValues(alpha: 0.09),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: riskColor.withValues(alpha: 0.3)),
            ),
            child: Row(
              children: [
                Icon(Icons.warning_amber_rounded, color: riskColor, size: 25),
                const SizedBox(width: 11),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Operational Risk',
                        style: TextStyle(
                          color: AppTheme.textSecondaryColor,
                          fontSize: 11,
                        ),
                      ),
                      const SizedBox(height: 3),
                      Text(
                        riskLevel.toUpperCase(),
                        style: TextStyle(
                          color: riskColor,
                          fontSize: 16,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ],
                  ),
                ),
                _StatusBadge(text: 'FACTOR: $dominantFactor', color: riskColor),
              ],
            ),
          ),
          const SizedBox(height: 14),

          _InfoRow(label: 'Recommended response', value: responseAction),
          const SizedBox(height: 10),
          _InfoRow(label: 'Response priority', value: responsePriority),
          const SizedBox(height: 10),
          _InfoRow(
            label: 'Human review',
            value: humanReviewRequired ? 'REQUIRED' : 'NOT REQUIRED',
          ),
          const SizedBox(height: 10),
          _InfoRow(
            label: 'Autonomous emergency action',
            value: autonomousAction ? 'ENABLED' : 'DISABLED',
          ),
          const SizedBox(height: 14),

          const Text(
            'Risk explanation',
            style: TextStyle(
              color: AppTheme.textSecondaryColor,
              fontSize: 11,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 5),
          Text(
            riskReason,
            style: const TextStyle(
              color: AppTheme.textPrimaryColor,
              fontSize: 12,
              height: 1.5,
            ),
          ),

          if (intelligenceError != null) ...[
            const SizedBox(height: 10),
            const Text(
              'Refresh failed. Displayed values may be stale.',
              style: TextStyle(color: AppTheme.warningColor, fontSize: 11),
            ),
          ],

          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: Text(
                  'Data: ${data['data_source'] ?? 'unknown'}',
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: AppTheme.textSecondaryColor,
                    fontSize: 9,
                  ),
                ),
              ),
              IconButton(
                tooltip: 'Refresh intelligence',
                onPressed: selectedCameraId == null
                    ? null
                    : () => _loadCameraIntelligence(selectedCameraId!),
                icon: const Icon(Icons.refresh, color: AppTheme.primaryColor),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _panel({required Widget child}) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(17),
      decoration: BoxDecoration(
        color: AppTheme.surfaceColor,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppTheme.borderColor),
      ),
      child: child,
    );
  }

  // ============================================================
  // SAFETY NOTICE
  // ============================================================

  Widget _buildSafetyNotice(CameraModel? camera) {
    final sourceType = camera?.sourceType.toLowerCase() ?? '';

    final message =
        sourceType.contains('recorded') || sourceType.contains('video')
        ? 'This camera uses a recorded video source. '
              'Its displayed intelligence reflects the backend replay data. '
              'Use risk information for human-reviewed decision support.'
        : 'Camera intelligence is intended for human-reviewed '
              'decision support. Verify the camera feed and surrounding '
              'conditions before taking operational action.';

    return Container(
      padding: const EdgeInsets.all(15),
      decoration: BoxDecoration(
        color: AppTheme.surfaceLightColor.withValues(alpha: 0.45),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppTheme.borderColor),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(
            Icons.info_outline,
            color: AppTheme.textSecondaryColor,
            size: 19,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              message,
              style: const TextStyle(
                color: AppTheme.textSecondaryColor,
                fontSize: 11,
                height: 1.5,
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ============================================================
  // ERROR
  // ============================================================

  Widget _buildError() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Container(
          padding: const EdgeInsets.all(22),
          decoration: BoxDecoration(
            color: AppTheme.surfaceColor,
            borderRadius: BorderRadius.circular(18),
            border: Border.all(
              color: AppTheme.dangerColor.withValues(alpha: 0.3),
            ),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(
                Icons.videocam_off_outlined,
                color: AppTheme.dangerColor,
                size: 42,
              ),
              const SizedBox(height: 12),
              const Text(
                'Unable to load cameras',
                style: TextStyle(
                  color: AppTheme.textPrimaryColor,
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 7),
              Text(
                errorMessage ?? 'Unknown camera error.',
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: AppTheme.textSecondaryColor,
                  fontSize: 11,
                  height: 1.4,
                ),
              ),
              const SizedBox(height: 15),
              ElevatedButton.icon(
                onPressed: _loadCameras,
                icon: const Icon(Icons.refresh, size: 17),
                label: const Text('Retry'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // ============================================================
  // EMPTY
  // ============================================================

  Widget _buildEmpty() {
    return const Center(
      child: Padding(
        padding: EdgeInsets.all(24),
        child: Text(
          'No camera sources are currently available.',
          textAlign: TextAlign.center,
          style: TextStyle(color: AppTheme.textSecondaryColor),
        ),
      ),
    );
  }

  // ============================================================
  // HELPERS
  // ============================================================

  static Map<String, dynamic> _asMap(dynamic value) {
    if (value is Map) {
      return Map<String, dynamic>.from(value);
    }
    return <String, dynamic>{};
  }

  static int _toInt(dynamic value) {
    if (value is num) return value.toInt();
    return int.tryParse(value?.toString() ?? '') ?? 0;
  }

  static double _toDouble(dynamic value) {
    if (value is num) return value.toDouble();
    return double.tryParse(value?.toString() ?? '') ?? 0.0;
  }

  static Color _riskColor(String level) {
    switch (level.toUpperCase()) {
      case 'LOW':
        return AppTheme.successColor;
      case 'MODERATE':
        return AppTheme.warningColor;
      case 'HIGH':
        return Colors.deepOrange;
      case 'CRITICAL':
        return AppTheme.criticalColor;
      default:
        return AppTheme.textSecondaryColor;
    }
  }

  static Color _statusColor(String status) {
    switch (status.toUpperCase()) {
      case 'RUNNING':
        return AppTheme.successColor;
      case 'RECORDED_REPLAY':
        return AppTheme.warningColor;
      case 'CONNECTING':
        return AppTheme.primaryColor;
      case 'ERROR':
      case 'FAILED':
        return AppTheme.dangerColor;
      default:
        return AppTheme.textSecondaryColor;
    }
  }
}

// ================================================================
// CAMERA CARD
// ================================================================

class _CameraCard extends StatelessWidget {
  const _CameraCard({
    required this.camera,
    required this.selected,
    required this.onTap,
  });

  final CameraModel camera;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final statusColor = _statusColorForCard(camera.status);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(18),
      child: Container(
        padding: const EdgeInsets.all(17),
        decoration: BoxDecoration(
          color: AppTheme.surfaceColor,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(
            color: selected ? AppTheme.primaryColor : AppTheme.borderColor,
            width: selected ? 1.5 : 1,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 45,
                  height: 45,
                  decoration: BoxDecoration(
                    color: AppTheme.primaryColor.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(
                    Icons.videocam,
                    color: AppTheme.primaryColor,
                    size: 23,
                  ),
                ),
                const SizedBox(width: 11),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        camera.cameraName,
                        style: const TextStyle(
                          color: AppTheme.textPrimaryColor,
                          fontSize: 15,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 3),
                      Text(
                        camera.cameraId,
                        style: const TextStyle(
                          color: AppTheme.textSecondaryColor,
                          fontSize: 10,
                        ),
                      ),
                    ],
                  ),
                ),
                _StatusBadge(text: camera.status, color: statusColor),
              ],
            ),
            const SizedBox(height: 18),
            _InfoRow(
              label: 'Source File',
              value: camera.sourceFile.isEmpty
                  ? 'Not specified'
                  : camera.sourceFile,
            ),
            const SizedBox(height: 11),
            _InfoRow(label: 'Source Type', value: camera.sourceType),
            const SizedBox(height: 11),
            _InfoRow(
              label: 'Resolution',
              value: '${camera.width} × ${camera.height}',
            ),
            const SizedBox(height: 11),
            _InfoRow(
              label: 'Frame Rate',
              value: '${camera.fps.toStringAsFixed(1)} FPS',
            ),
            const SizedBox(height: 11),
            _InfoRow(label: 'Frame Count', value: camera.frameCount.toString()),
            const SizedBox(height: 11),
            _InfoRow(
              label: 'Duration',
              value: '${camera.durationSeconds.toStringAsFixed(2)} sec',
            ),
            const SizedBox(height: 11),
            _InfoRow(
              label: 'Live Stream',
              value: camera.liveStream ? 'YES' : 'NO',
            ),
            const SizedBox(height: 11),
            _InfoRow(
              label: 'Human Review',
              value: camera.humanReviewRequired ? 'REQUIRED' : 'NOT REQUIRED',
            ),
            const SizedBox(height: 11),
            _InfoRow(
              label: 'Autonomous Action',
              value: camera.autonomousEmergencyAction ? 'ENABLED' : 'DISABLED',
            ),
            if (selected) ...[
              const SizedBox(height: 14),
              const Row(
                children: [
                  Icon(
                    Icons.check_circle,
                    color: AppTheme.primaryColor,
                    size: 16,
                  ),
                  SizedBox(width: 7),
                  Text(
                    'Selected for intelligence monitoring',
                    style: TextStyle(
                      color: AppTheme.primaryColor,
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  static Color _statusColorForCard(String status) {
    switch (status.toUpperCase()) {
      case 'RUNNING':
        return AppTheme.successColor;
      case 'RECORDED_REPLAY':
        return AppTheme.warningColor;
      case 'CONNECTING':
        return AppTheme.primaryColor;
      case 'ERROR':
      case 'FAILED':
        return AppTheme.dangerColor;
      default:
        return AppTheme.textSecondaryColor;
    }
  }
}

// ================================================================
// METRIC CARD
// ================================================================

class _MetricCard extends StatelessWidget {
  const _MetricCard({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
    this.footer,
  });

  final String label;
  final String value;
  final IconData icon;
  final Color color;
  final String? footer;

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: const BoxConstraints(minHeight: 112),
      padding: const EdgeInsets.all(13),
      decoration: BoxDecoration(
        color: AppTheme.surfaceLightColor.withValues(alpha: 0.48),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppTheme.borderColor),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 34,
            height: 34,
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: color, size: 19),
          ),
          const SizedBox(height: 11),
          FittedBox(
            fit: BoxFit.scaleDown,
            alignment: Alignment.centerLeft,
            child: Text(
              value,
              maxLines: 1,
              style: TextStyle(
                color: color,
                fontSize: 23,
                fontWeight: FontWeight.w800,
              ),
            ),
          ),
          if (footer != null) ...[
            const SizedBox(height: 2),
            Text(
              footer!,
              style: const TextStyle(
                color: AppTheme.textSecondaryColor,
                fontSize: 9,
              ),
            ),
          ],
          const SizedBox(height: 5),
          Text(
            label,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              color: AppTheme.textSecondaryColor,
              fontSize: 10,
              height: 1.25,
            ),
          ),
        ],
      ),
    );
  }
}

// ================================================================
// SECTION HEADER
// ================================================================

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({required this.title, required this.icon});

  final String title;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, color: AppTheme.primaryColor, size: 18),
        const SizedBox(width: 8),
        Text(
          title,
          style: const TextStyle(
            color: AppTheme.textPrimaryColor,
            fontSize: 16,
            fontWeight: FontWeight.w700,
          ),
        ),
      ],
    );
  }
}

// ================================================================
// INFO ROW
// ================================================================

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          flex: 4,
          child: Text(
            label,
            style: const TextStyle(
              color: AppTheme.textSecondaryColor,
              fontSize: 11,
            ),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          flex: 6,
          child: Text(
            value,
            textAlign: TextAlign.right,
            style: const TextStyle(
              color: AppTheme.textPrimaryColor,
              fontSize: 11,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
      ],
    );
  }
}

// ================================================================
// STATUS BADGE
// ================================================================

class _StatusBadge extends StatelessWidget {
  const _StatusBadge({required this.text, required this.color});

  final String text;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.25)),
      ),
      child: Text(
        text.replaceAll('_', ' ').toUpperCase(),
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: TextStyle(
          color: color,
          fontSize: 9,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}
