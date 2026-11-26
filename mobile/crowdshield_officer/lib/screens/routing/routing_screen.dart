import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';

import '../../services/api_service.dart';

class RoutingScreen extends StatefulWidget {
  const RoutingScreen({super.key});

  @override
  State<RoutingScreen> createState() => _RoutingScreenState();
}

class _RoutingScreenState extends State<RoutingScreen> {
  final ApiService _apiService = ApiService();

  bool _loading = true;
  String? _error;

  Map<String, dynamic>? _routeData;
  Map<String, dynamic>? _validationData;

  @override
  void initState() {
    super.initState();
    _loadRouting();
  }

  Future<void> _loadRouting() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final results = await Future.wait([
        _apiService.getSimulatedRoute(),
        _apiService.getRouteValidation(),
      ]);

      if (!mounted) return;

      setState(() {
        _routeData = results[0];
        _validationData = results[1];
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _loading = false;
        _error = e.toString();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      appBar: AppBar(
        backgroundColor: AppTheme.backgroundColor,
        elevation: 0,
        title: const Text(
          'Emergency Routing',
          style: TextStyle(
            color: AppTheme.textPrimaryColor,
            fontWeight: FontWeight.w700,
          ),
        ),
        actions: [
          IconButton(
            onPressed: _loading ? null : _loadRouting,
            icon: const Icon(
              Icons.refresh_rounded,
              color: AppTheme.textPrimaryColor,
            ),
          ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_loading) {
      return const Center(
        child: CircularProgressIndicator(
          color: AppTheme.primaryColor,
        ),
      );
    }

    if (_error != null) {
      return _buildError();
    }

    return RefreshIndicator(
      color: AppTheme.primaryColor,
      backgroundColor: AppTheme.surfaceColor,
      onRefresh: _loadRouting,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
        children: [
          _buildSimulationBanner(),
          const SizedBox(height: 16),
          _buildRouteOverview(),
          const SizedBox(height: 16),
          _buildValidationCard(),
          const SizedBox(height: 16),
          _buildRouteDetails(),
          const SizedBox(height: 16),
          _buildRoutePath(),
          const SizedBox(height: 16),
          _buildSafetyDisclaimer(),
        ],
      ),
    );
  }

  Widget _buildSimulationBanner() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.warningColor.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppTheme.warningColor.withValues(alpha: 0.35),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: AppTheme.warningColor.withValues(alpha: 0.15),
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.warning_amber_rounded,
              color: AppTheme.warningColor,
              size: 22,
            ),
          ),
          const SizedBox(width: 12),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'SIMULATION / DEMONSTRATION',
                  style: TextStyle(
                    color: AppTheme.warningColor,
                    fontSize: 13,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 0.5,
                  ),
                ),
                SizedBox(height: 6),
                Text(
                  'This route is generated using a synthetic A* simulation. '
                  'It is not a real-world or safety-validated evacuation route.',
                  style: TextStyle(
                    color: AppTheme.textSecondaryColor,
                    fontSize: 12,
                    height: 1.5,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRouteOverview() {
    final routeType =
        _routeData?['route_type']?.toString() ?? 'Simulated A* route';

    final status =
        _routeData?['status']?.toString() ?? 'Demonstration only';

    final frame = _routeData?['frame'];

    final route = _routeData?['route'];

    final routePoints = route is List ? route.length : 0;

    return _Card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const _SectionTitle(
            icon: Icons.alt_route_rounded,
            title: 'Route Overview',
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: _MetricBox(
                  label: 'Route Type',
                  value: 'A*',
                  icon: Icons.route_rounded,
                  iconColor: AppTheme.primaryColor,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _MetricBox(
                  label: 'Route Points',
                  value: '$routePoints',
                  icon: Icons.polyline_rounded,
                  iconColor: AppTheme.successColor,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: _MetricBox(
                  label: 'Frame',
                  value: frame?.toString() ?? '--',
                  icon: Icons.video_camera_back_rounded,
                  iconColor: AppTheme.warningColor,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _MetricBox(
                  label: 'Status',
                  value: _shortStatus(status),
                  icon: Icons.info_outline_rounded,
                  iconColor: AppTheme.warningColor,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          _InfoRow(
            label: 'Algorithm',
            value: routeType,
          ),
          const SizedBox(height: 10),
          _InfoRow(
            label: 'Operational Status',
            value: status,
          ),
        ],
      ),
    );
  }

  Widget _buildValidationCard() {
    final validation = _validationData ?? {};

    final validationStatus =
        validation['status']?.toString() ?? 'Simulation only';

    final obstacleValidation =
        validation['obstacle_validation']?.toString() ??
            validation['obstacle_check']?.toString() ??
            'Not available';

    final continuityValidation =
        validation['continuity_validation']?.toString() ??
            validation['continuity_check']?.toString() ??
            'Not available';

    final blocked = _toInt(validation['blocked']);
    final invalidSteps =
        _toInt(validation['invalid_consecutive_steps']);

    final passed = validationStatus.toUpperCase().contains('PASS');

    return _Card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const _SectionTitle(
            icon: Icons.fact_check_rounded,
            title: 'Route Validation',
          ),
          const SizedBox(height: 16),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: (passed
                      ? AppTheme.successColor
                      : AppTheme.warningColor)
                  .withValues(alpha: 0.10),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: (passed
                        ? AppTheme.successColor
                        : AppTheme.warningColor)
                    .withValues(alpha: 0.25),
              ),
            ),
            child: Row(
              children: [
                Icon(
                  passed
                      ? Icons.check_circle_rounded
                      : Icons.info_rounded,
                  color: passed
                      ? AppTheme.successColor
                      : AppTheme.warningColor,
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    validationStatus,
                    style: TextStyle(
                      color: passed
                          ? AppTheme.successColor
                          : AppTheme.warningColor,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),
          _ValidationRow(
            label: 'Obstacle Validation',
            value: obstacleValidation,
          ),
          _ValidationRow(
            label: 'Continuity Validation',
            value: continuityValidation,
          ),
          _ValidationRow(
            label: 'Blocked Points',
            value: '$blocked',
          ),
          _ValidationRow(
            label: 'Invalid Consecutive Steps',
            value: '$invalidSteps',
          ),
        ],
      ),
    );
  }

  Widget _buildRouteDetails() {
    final route = _routeData?['route'];

    String startPoint = '--';
    String endPoint = '--';

    if (route is List && route.isNotEmpty) {
      startPoint = _formatPoint(route.first);
      endPoint = _formatPoint(route.last);
    }

    return _Card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const _SectionTitle(
            icon: Icons.pin_drop_rounded,
            title: 'Route Details',
          ),
          const SizedBox(height: 16),
          _RoutePoint(
            icon: Icons.trip_origin_rounded,
            title: 'Start Point',
            value: startPoint,
          ),
          const SizedBox(height: 12),
          _RoutePoint(
            icon: Icons.location_on_rounded,
            title: 'Destination',
            value: endPoint,
          ),
        ],
      ),
    );
  }

  Widget _buildRoutePath() {
    final route = _routeData?['route'];

    final points = <String>[];

    if (route is List) {
      for (final point in route.take(8)) {
        points.add(_formatPoint(point));
      }
    }

    return _Card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const _SectionTitle(
            icon: Icons.timeline_rounded,
            title: 'Simulated Route Path',
          ),
          const SizedBox(height: 8),
          const Text(
            'Sample route coordinates from the synthetic grid.',
            style: TextStyle(
              color: AppTheme.textSecondaryColor,
              fontSize: 12,
            ),
          ),
          const SizedBox(height: 14),
          if (points.isEmpty)
            const Text(
              'No route points available.',
              style: TextStyle(
                color: AppTheme.textSecondaryColor,
              ),
            )
          else
            ...List.generate(
              points.length,
              (index) => _PathPoint(
                index: index + 1,
                value: points[index],
                isLast: index == points.length - 1,
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildSafetyDisclaimer() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surfaceColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppTheme.borderColor,
        ),
      ),
      child: const Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            Icons.shield_outlined,
            color: AppTheme.primaryColor,
            size: 22,
          ),
          SizedBox(width: 12),
          Expanded(
            child: Text(
              'Officer decision support only. The current routing '
              'implementation uses a synthetic grid and has not been '
              'validated against a real road network or real evacuation '
              'conditions. Human review is required before any operational use.',
              style: TextStyle(
                color: AppTheme.textSecondaryColor,
                fontSize: 12,
                height: 1.5,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildError() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: _Card(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(
                Icons.cloud_off_rounded,
                color: AppTheme.dangerColor,
                size: 48,
              ),
              const SizedBox(height: 16),
              const Text(
                'Unable to load routing data',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: AppTheme.textPrimaryColor,
                  fontSize: 17,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                _error ?? 'Unknown error',
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: AppTheme.textSecondaryColor,
                  fontSize: 12,
                ),
              ),
              const SizedBox(height: 20),
              ElevatedButton.icon(
                onPressed: _loadRouting,
                icon: const Icon(Icons.refresh_rounded),
                label: const Text('Retry'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  int _toInt(dynamic value) {
    if (value is int) return value;
    return int.tryParse(value?.toString() ?? '') ?? 0;
  }

  String _formatPoint(dynamic point) {
    if (point is List && point.length >= 2) {
      return '[${point[0]}, ${point[1]}]';
    }

    if (point is Map) {
      final x = point['x'] ?? point['X'] ?? point['lon'] ?? point['longitude'];
      final y = point['y'] ?? point['Y'] ?? point['lat'] ?? point['latitude'];

      if (x != null && y != null) {
        return '[$x, $y]';
      }
    }

    return point?.toString() ?? '--';
  }

  String _shortStatus(String value) {
    if (value.length <= 18) return value;
    return '${value.substring(0, 15)}...';
  }
}

class _Card extends StatelessWidget {
  final Widget child;

  const _Card({
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surfaceColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppTheme.borderColor,
        ),
      ),
      child: child,
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final IconData icon;
  final String title;

  const _SectionTitle({
    required this.icon,
    required this.title,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(
          icon,
          color: AppTheme.primaryColor,
          size: 21,
        ),
        const SizedBox(width: 9),
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

class _MetricBox extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color iconColor;

  const _MetricBox({
    required this.label,
    required this.value,
    required this.icon,
    required this.iconColor,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppTheme.surfaceLightColor,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            icon,
            color: iconColor,
            size: 20,
          ),
          const SizedBox(height: 10),
          Text(
            value,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              color: AppTheme.textPrimaryColor,
              fontSize: 16,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 3),
          Text(
            label,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              color: AppTheme.textSecondaryColor,
              fontSize: 10,
            ),
          ),
        ],
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final String label;
  final String value;

  const _InfoRow({
    required this.label,
    required this.value,
  });

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
              fontSize: 12,
            ),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          flex: 6,
          child: Text(
            value,
            textAlign: TextAlign.right,
            style: const TextStyle(
              color: AppTheme.textPrimaryColor,
              fontSize: 12,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
      ],
    );
  }
}

class _ValidationRow extends StatelessWidget {
  final String label;
  final String value;

  const _ValidationRow({
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    final isPass = value.toUpperCase().contains('PASS');

    return Padding(
      padding: const EdgeInsets.only(bottom: 11),
      child: Row(
        children: [
          Expanded(
            child: Text(
              label,
              style: const TextStyle(
                color: AppTheme.textSecondaryColor,
                fontSize: 12,
              ),
            ),
          ),
          Flexible(
            child: Text(
              value,
              textAlign: TextAlign.right,
              style: TextStyle(
                color: isPass
                    ? AppTheme.successColor
                    : AppTheme.textPrimaryColor,
                fontSize: 12,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _RoutePoint extends StatelessWidget {
  final IconData icon;
  final String title;
  final String value;

  const _RoutePoint({
    required this.icon,
    required this.title,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(
          icon,
          color: AppTheme.primaryColor,
          size: 22,
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  color: AppTheme.textSecondaryColor,
                  fontSize: 11,
                ),
              ),
              const SizedBox(height: 3),
              Text(
                value,
                style: const TextStyle(
                  color: AppTheme.textPrimaryColor,
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _PathPoint extends StatelessWidget {
  final int index;
  final String value;
  final bool isLast;

  const _PathPoint({
    required this.index,
    required this.value,
    required this.isLast,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Column(
          children: [
            Container(
              width: 26,
              height: 26,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: AppTheme.primaryColor.withValues(alpha: 0.12),
                shape: BoxShape.circle,
              ),
              child: Text(
                '$index',
                style: const TextStyle(
                  color: AppTheme.primaryColor,
                  fontSize: 10,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
            if (!isLast)
              Container(
                width: 1,
                height: 22,
                color: AppTheme.borderColor,
              ),
          ],
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Padding(
            padding: const EdgeInsets.only(top: 5),
            child: Text(
              value,
              style: const TextStyle(
                color: AppTheme.textPrimaryColor,
                fontSize: 12,
              ),
            ),
          ),
        ),
      ],
    );
  }
}