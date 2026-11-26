import 'package:flutter/material.dart';

import '../core/theme/app_theme.dart';
import '../models/alert_model.dart';
import '../models/dashboard_model.dart';
import '../models/risk_model.dart';
import '../models/system_model.dart';
import '../screens/cameras/camera_monitoring_screen.dart';
import '../screens/response/response_screen.dart';
import '../screens/routing/routing_screen.dart';
import '../services/api_service.dart';

class CrowdShieldApp extends StatelessWidget {
  const CrowdShieldApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'CrowdShield Officer',
      theme: AppTheme.darkTheme,
      home: const OfficerHomePage(),
    );
  }
}

class OfficerHomePage extends StatefulWidget {
  const OfficerHomePage({super.key});

  @override
  State<OfficerHomePage> createState() => _OfficerHomePageState();
}

class _OfficerHomePageState extends State<OfficerHomePage> {
  final ApiService _apiService = ApiService();

  int _currentIndex = 0;

  DashboardModel? _dashboard;
  List<AlertModel> _alerts = [];

  SystemHealthModel? _systemHealth;
  DatabaseHealthModel? _databaseHealth;
  CameraResponseModel? _cameraResponse;

  bool _loading = true;
  bool _alertsLoading = true;
  bool _systemLoading = true;

  String? _dashboardError;
  String? _alertsError;
  String? _systemError;

  @override
  void initState() {
    super.initState();
    _loadAll();
  }

  Future<void> _loadAll() async {
    await Future.wait([
      _loadDashboard(),
      _loadAlerts(),
      _loadSystem(),
    ]);
  }

  Future<void> _refreshAll() async {
    await _loadAll();
  }

  Future<void> _loadDashboard() async {
    if (mounted) {
      setState(() {
        _loading = true;
        _dashboardError = null;
      });
    }

    try {
      final data = await _apiService.getDashboardSummary();

      if (!mounted) return;

      setState(() {
        _dashboard = DashboardModel.fromJson(data);
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _loading = false;
        _dashboardError = e.toString();
      });
    }
  }

  Future<void> _loadAlerts() async {
    if (mounted) {
      setState(() {
        _alertsLoading = true;
        _alertsError = null;
      });
    }

    try {
      final alerts = await _apiService.getAlerts();

      if (!mounted) return;

      setState(() {
        _alerts = alerts;
        _alertsLoading = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _alertsLoading = false;
        _alertsError = e.toString();
      });
    }
  }

  Future<void> _loadSystem() async {
    if (mounted) {
      setState(() {
        _systemLoading = true;
        _systemError = null;
      });
    }

    try {
      final results = await Future.wait([
        _apiService.getHealth(),
        _apiService.getDatabaseHealth(),
        _apiService.getCameras(),
      ]);

      if (!mounted) return;

      setState(() {
        _systemHealth = SystemHealthModel.fromJson(results[0]);
        _databaseHealth = DatabaseHealthModel.fromJson(results[1]);
        _cameraResponse = CameraResponseModel.fromJson(results[2]);
        _systemLoading = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _systemLoading = false;
        _systemError = e.toString();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final pages = <Widget>[
      _buildDashboard(),
      _buildAlerts(),
      _buildRiskMonitoring(),
      const CameraMonitoringScreen(),
      const ResponseScreen(),
      const RoutingScreen(),
      _buildSystemStatus(),
    ];

    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      body: SafeArea(
        child: IndexedStack(
          index: _currentIndex,
          children: pages,
        ),
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        backgroundColor: AppTheme.surfaceColor,
        indicatorColor: AppTheme.primaryColor.withValues(alpha: 0.15),
        labelTextStyle: WidgetStateProperty.all(
          const TextStyle(
            fontSize: 10,
            fontWeight: FontWeight.w600,
          ),
        ),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.dashboard_outlined),
            selectedIcon: Icon(Icons.dashboard_rounded),
            label: 'Dashboard',
          ),
          NavigationDestination(
            icon: Icon(Icons.notifications_none_rounded),
            selectedIcon: Icon(Icons.notifications_rounded),
            label: 'Alerts',
          ),
          NavigationDestination(
            icon: Icon(Icons.analytics_outlined),
            selectedIcon: Icon(Icons.analytics_rounded),
            label: 'Risk',
          ),
          NavigationDestination(
            icon: Icon(Icons.videocam_outlined),
            selectedIcon: Icon(Icons.videocam_rounded),
            label: 'Camera',
          ),
          NavigationDestination(
            icon: Icon(Icons.shield_outlined),
            selectedIcon: Icon(Icons.shield_rounded),
            label: 'Response',
          ),
          NavigationDestination(
            icon: Icon(Icons.alt_route_outlined),
            selectedIcon: Icon(Icons.alt_route_rounded),
            label: 'Routing',
          ),
          NavigationDestination(
            icon: Icon(Icons.settings_outlined),
            selectedIcon: Icon(Icons.settings_rounded),
            label: 'System',
          ),
        ],
      ),
    );
  }

  // ============================================================
  // DASHBOARD
  // ============================================================

  Widget _buildDashboard() {
    if (_loading) return _buildLoading('Loading officer dashboard...');
    if (_dashboardError != null) {
      return _buildError(
        title: 'Unable to load dashboard',
        message: _dashboardError!,
        onRetry: _loadDashboard,
      );
    }
    final dashboard = _dashboard;
    if (dashboard == null) {
      return _buildError(
        title: 'No dashboard data',
        message: 'The backend did not return dashboard information.',
        onRetry: _loadDashboard,
      );
    }
    return RefreshIndicator(
      color: AppTheme.primaryColor,
      backgroundColor: AppTheme.surfaceColor,
      onRefresh: _refreshAll,
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(16, 18, 16, 28),
        children: [
          _buildHeader(
            title: 'Officer Command Center',
            subtitle: 'CROWDSHIELD AI  •  OPERATIONAL OVERVIEW',
            icon: Icons.shield_rounded,
          ),
          const SizedBox(height: 20),
          _buildCurrentRiskCard(dashboard.latestState),
          const SizedBox(height: 16),
          _buildDashboardStats(dashboard),
          const SizedBox(height: 18),
          _buildRiskDistribution(dashboard),
          const SizedBox(height: 16),
          _buildResponseDistribution(dashboard),
          const SizedBox(height: 16),
          _buildSafetyControls(dashboard),
          const SizedBox(height: 16),
          const _DisclaimerCard(
            text: 'Operational risk is a rule-based decision-support score, not a probability and not a validated emergency prediction. Human review is required.',
          ),
        ],
      ),
    );
  }

  Widget _buildHeader({
    required String title,
    required String subtitle,
    required IconData icon,
  }) {
    return Row(
      children: [
        Container(
          width: 46,
          height: 46,
          decoration: BoxDecoration(
            color: AppTheme.primaryColor.withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(13),
          ),
          child: Icon(
            icon,
            color: AppTheme.primaryColor,
            size: 25,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  color: AppTheme.textPrimaryColor,
                  fontSize: 20,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 3),
              Text(
                subtitle,
                style: const TextStyle(
                  color: AppTheme.textSecondaryColor,
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildCurrentRiskCard(dynamic latest) {
    final riskLevel = _text(latest.riskLevel);
    final response = _text(latest.responseAction);
    final priority = _text(latest.responsePriority);
    final window = _text(latest.windowId);
    final score = _number(latest.riskScore).clamp(0.0, 100.0);
    final color = _riskColor(riskLevel);

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            AppTheme.surfaceColor,
            color.withValues(alpha: 0.09),
          ],
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withValues(alpha: 0.38)),
        boxShadow: [
          BoxShadow(
            color: color.withValues(alpha: 0.07),
            blurRadius: 22,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Expanded(
                child: Text(
                  'CURRENT OPERATIONAL RISK',
                  style: TextStyle(
                    color: AppTheme.textSecondaryColor,
                    fontSize: 10,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 1.0,
                  ),
                ),
              ),
              _StatusChip(text: riskLevel, color: color),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                score.toStringAsFixed(1),
                style: TextStyle(
                  color: color,
                  fontSize: 43,
                  height: 1,
                  fontWeight: FontWeight.w900,
                  letterSpacing: -1.2,
                ),
              ),
              const Padding(
                padding: EdgeInsets.only(bottom: 5, left: 8),
                child: Text(
                  '/ 100',
                  style: TextStyle(
                    color: AppTheme.textSecondaryColor,
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 15),
          ClipRRect(
            borderRadius: BorderRadius.circular(20),
            child: LinearProgressIndicator(
              value: score / 100.0,
              minHeight: 7,
              backgroundColor: AppTheme.borderColor,
              valueColor: AlwaysStoppedAnimation<Color>(color),
            ),
          ),
          const SizedBox(height: 17),
          const Divider(color: AppTheme.borderColor, height: 1),
          const SizedBox(height: 14),
          _InfoRow(label: 'Recommended response', value: response),
          const SizedBox(height: 10),
          _InfoRow(label: 'Response priority', value: priority),
          const SizedBox(height: 10),
          _InfoRow(label: 'Monitoring window', value: window),
        ],
      ),
    );
  }

  Widget _buildDashboardStats(DashboardModel dashboard) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(child: _StatCard(
          title: 'Windows',
          value: _text(dashboard.processedWindows),
          icon: Icons.view_timeline_rounded,
          color: AppTheme.primaryColor,
        )),
        const SizedBox(width: 9),
        Expanded(child: _StatCard(
          title: 'Mean Risk',
          value: _number(dashboard.meanRiskScore).toStringAsFixed(1),
          icon: Icons.insights_rounded,
          color: AppTheme.warningColor,
        )),
        const SizedBox(width: 9),
        Expanded(child: _StatCard(
          title: 'Max Risk',
          value: _number(dashboard.maximumRiskScore).toStringAsFixed(1),
          icon: Icons.trending_up_rounded,
          color: AppTheme.dangerColor,
        )),
      ],
    );
  }

  Widget _buildRiskDistribution(DashboardModel dashboard) {
    final distribution = dashboard.riskDistribution;
    final low = _count(distribution['LOW']);
    final moderate = _count(distribution['MODERATE']);
    final high = _count(distribution['HIGH']);
    final critical = _count(distribution['CRITICAL']);
    final total = low + moderate + high + critical;

    return _SectionCard(
      title: 'Risk Distribution',
      icon: Icons.donut_large_rounded,
      child: Column(
        children: [
          _DistributionRow(label: 'LOW', value: low, total: total, color: AppTheme.successColor),
          _DistributionRow(label: 'MODERATE', value: moderate, total: total, color: AppTheme.warningColor),
          _DistributionRow(label: 'HIGH', value: high, total: total, color: AppTheme.dangerColor),
          _DistributionRow(label: 'CRITICAL', value: critical, total: total, color: AppTheme.criticalColor),
        ],
      ),
    );
  }

  Widget _buildResponseDistribution(DashboardModel dashboard) {
    if (dashboard.responseDistribution.isEmpty) return const SizedBox.shrink();
    final entries = dashboard.responseDistribution.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));
    final total = entries.fold<int>(0, (sum, entry) => sum + _count(entry.value));

    return _SectionCard(
      title: 'Response Distribution',
      icon: Icons.rule_rounded,
      child: Column(
        children: entries.map((entry) => _DistributionRow(
          label: _text(entry.key),
          value: _count(entry.value),
          total: total,
          color: _priorityColor(_text(entry.key)),
        )).toList(),
      ),
    );
  }

  Widget _buildSafetyControls(DashboardModel dashboard) {
    return _SectionCard(
      title: 'Safety Controls',
      icon: Icons.security_rounded,
      child: Column(
        children: [
          _ControlRow(
            label: 'Human Review',
            value: dashboard.humanReviewRequired ? 'REQUIRED' : 'NOT REQUIRED',
            enabled: dashboard.humanReviewRequired,
            color: AppTheme.warningColor,
          ),
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 12),
            child: Divider(color: AppTheme.borderColor, height: 1),
          ),
          _ControlRow(
            label: 'Autonomous Emergency Action',
            value: dashboard.autonomousEmergencyAction ? 'ENABLED' : 'DISABLED',
            enabled: dashboard.autonomousEmergencyAction,
            color: dashboard.autonomousEmergencyAction ? AppTheme.dangerColor : AppTheme.successColor,
          ),
        ],
      ),
    );
  }

  // ============================================================
  // ALERTS
  // ============================================================

  Widget _buildAlerts() {
    if (_alertsLoading) {
      return _buildLoading('Loading operational alerts...');
    }

    if (_alertsError != null) {
      return _buildError(
        title: 'Unable to load alerts',
        message: _alertsError!,
        onRetry: _loadAlerts,
      );
    }

    final highPriorityCount = _alerts.where((alert) {
      final level = _text(alert.operationalRiskLevel).toUpperCase();
      return level == 'HIGH' || level == 'CRITICAL';
    }).length;

    return RefreshIndicator(
      color: AppTheme.primaryColor,
      backgroundColor: AppTheme.surfaceColor,
      onRefresh: _loadAlerts,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
        children: [
          _buildHeader(
            title: 'Operational Alerts',
            subtitle: 'LIVE FEED  •  DECISION SUPPORT',
            icon: Icons.notifications_active_rounded,
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: _StatCard(
                  title: 'Total Alerts',
                  value: _alerts.length.toString(),
                  icon: Icons.notifications_none_rounded,
                  color: AppTheme.primaryColor,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _StatCard(
                  title: 'High / Critical',
                  value: highPriorityCount.toString(),
                  icon: Icons.priority_high_rounded,
                  color: AppTheme.dangerColor,
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          Row(
            children: [
              const Expanded(
                child: Text(
                  'Alert Feed',
                  style: TextStyle(
                    color: AppTheme.textPrimaryColor,
                    fontSize: 17,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
              _StatusChip(
                text: _alerts.isEmpty ? 'CLEAR' : 'UPDATED',
                color: _alerts.isEmpty
                    ? AppTheme.successColor
                    : AppTheme.primaryColor,
              ),
            ],
          ),
          const SizedBox(height: 12),
          if (_alerts.isEmpty)
            _buildEmptyState(
              icon: Icons.notifications_none_rounded,
              title: 'No operational alerts',
              message: 'No alert records are currently available.',
            )
          else
            ..._alerts.map(_buildAlertCard),
          const SizedBox(height: 8),
          const _DisclaimerCard(
            text:
                'Alerts represent rule-based operational decision support. They are not autonomous emergency commands.',
          ),
        ],
      ),
    );
  }

  Widget _buildAlertCard(AlertModel alert) {
    final level = _text(alert.operationalRiskLevel);
    final color = _riskColor(level);
    final score = _number(alert.operationalRiskScore).clamp(0.0, 100.0);

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surfaceColor,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: color.withValues(alpha: 0.30)),
        boxShadow: [
          BoxShadow(
            color: color.withValues(alpha: 0.05),
            blurRadius: 14,
            offset: const Offset(0, 5),
          ),
        ],
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
                  color: color.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  Icons.notification_important_rounded,
                  color: color,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _text(alert.windowId),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: AppTheme.textPrimaryColor,
                        fontWeight: FontWeight.w800,
                        fontSize: 14,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Operational risk alert',
                      style: TextStyle(
                        color: AppTheme.textSecondaryColor,
                        fontSize: 11,
                      ),
                    ),
                  ],
                ),
              ),
              _StatusChip(text: level, color: color),
            ],
          ),
          const SizedBox(height: 18),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'RISK SCORE',
                      style: TextStyle(
                        color: AppTheme.textSecondaryColor,
                        fontSize: 10,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 0.8,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      score.toStringAsFixed(1),
                      style: TextStyle(
                        color: color,
                        fontSize: 29,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ],
                ),
              ),
              Flexible(
                child: _SmallValue(
                  label: 'Response',
                  value: _text(alert.responseAction),
                  color: AppTheme.primaryColor,
                ),
              ),
            ],
          ),
          const SizedBox(height: 9),
          ClipRRect(
            borderRadius: BorderRadius.circular(99),
            child: LinearProgressIndicator(
              value: score / 100.0,
              minHeight: 6,
              backgroundColor: AppTheme.borderColor,
              valueColor: AlwaysStoppedAnimation<Color>(color),
            ),
          ),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppTheme.surfaceLightColor,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Column(
              children: [
                _InfoRow(
                  label: 'Dominant Factor',
                  value: _text(alert.dominantRiskFactor),
                ),
                const SizedBox(height: 10),
                _InfoRow(
                  label: 'Priority',
                  value: _text(alert.responsePriority),
                ),
              ],
            ),
          ),
          const SizedBox(height: 13),
          Text(
            _text(alert.operationalRiskReason),
            style: const TextStyle(
              color: AppTheme.textSecondaryColor,
              fontSize: 12,
              height: 1.5,
            ),
          ),
          if (_text(alert.activeSignals).isNotEmpty) ...[
            const SizedBox(height: 12),
            _SignalChip(text: _text(alert.activeSignals)),
          ],
        ],
      ),
    );
  }

  // ============================================================
  // RISK MONITORING
  // ============================================================

  Widget _buildRiskMonitoring() {
    return FutureBuilder<List<RiskModel>>(
      future: _apiService.getRiskTimeline(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return _buildLoading('Loading risk timeline...');
        }

        if (snapshot.hasError) {
          return _buildError(
            title: 'Unable to load risk timeline',
            message: snapshot.error.toString(),
            onRetry: () {
              setState(() {});
            },
          );
        }

        final risks = snapshot.data ?? <RiskModel>[];
        final highRiskCount = risks.where((risk) {
          final level = _text(risk.operationalRiskLevel).toUpperCase();
          return level == 'HIGH' || level == 'CRITICAL';
        }).length;
        final averageScore = risks.isEmpty
            ? 0.0
            : risks.fold<double>(
                  0.0,
                  (sum, risk) => sum + _number(risk.operationalRiskScore),
                ) /
                risks.length;

        return RefreshIndicator(
          color: AppTheme.primaryColor,
          backgroundColor: AppTheme.surfaceColor,
          onRefresh: () async {
            setState(() {});
            await Future<void>.delayed(
              const Duration(milliseconds: 300),
            );
          },
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
            children: [
              _buildHeader(
                title: 'Risk Monitoring',
                subtitle: 'TEMPORAL ANALYSIS  •  RISK WINDOWS',
                icon: Icons.monitor_heart_rounded,
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: _StatCard(
                      title: 'Risk Windows',
                      value: risks.length.toString(),
                      icon: Icons.timeline_rounded,
                      color: AppTheme.primaryColor,
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: _StatCard(
                      title: 'High / Critical',
                      value: highRiskCount.toString(),
                      icon: Icons.warning_amber_rounded,
                      color: AppTheme.dangerColor,
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: _StatCard(
                      title: 'Mean Score',
                      value: averageScore.toStringAsFixed(1),
                      icon: Icons.insights_rounded,
                      color: AppTheme.warningColor,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),
              Row(
                children: [
                  const Expanded(
                    child: Text(
                      'Risk Timeline',
                      style: TextStyle(
                        color: AppTheme.textPrimaryColor,
                        fontSize: 17,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                  _StatusChip(
                    text: '${risks.length} WINDOWS',
                    color: AppTheme.primaryColor,
                  ),
                ],
              ),
              const SizedBox(height: 12),
              if (risks.isEmpty)
                _buildEmptyState(
                  icon: Icons.analytics_outlined,
                  title: 'No risk data',
                  message: 'The backend returned no risk windows.',
                )
              else
                ...risks.map(_buildRiskCard),
              const SizedBox(height: 8),
              _buildDisclaimerCard(
                title: 'Interpretation',
                text:
                    'The operational risk score is a rule-based decision-support measure. It is not a probability and is not a validated emergency prediction.',
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildRiskCard(RiskModel risk) {
    final level = _text(risk.operationalRiskLevel);
    final color = _riskColor(level);
    final score = _number(risk.operationalRiskScore).clamp(0.0, 100.0);

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surfaceColor,
        borderRadius: BorderRadius.circular(17),
        border: Border.all(color: AppTheme.borderColor),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 5,
                height: 48,
                decoration: BoxDecoration(
                  color: color,
                  borderRadius: BorderRadius.circular(99),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _text(risk.windowId),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: AppTheme.textPrimaryColor,
                        fontWeight: FontWeight.w800,
                        fontSize: 14,
                      ),
                    ),
                    const SizedBox(height: 5),
                    Text(
                      _text(risk.dominantRiskFactor),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: AppTheme.textSecondaryColor,
                        fontSize: 11,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    score.toStringAsFixed(1),
                    style: TextStyle(
                      color: color,
                      fontSize: 22,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  _StatusChip(text: level, color: color),
                ],
              ),
            ],
          ),
          const SizedBox(height: 14),
          ClipRRect(
            borderRadius: BorderRadius.circular(99),
            child: LinearProgressIndicator(
              value: score / 100.0,
              minHeight: 5,
              backgroundColor: AppTheme.borderColor,
              valueColor: AlwaysStoppedAnimation<Color>(color),
            ),
          ),
          const SizedBox(height: 12),
          Text(
            _text(risk.operationalRiskReason),
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              color: AppTheme.textSecondaryColor,
              fontSize: 12,
              height: 1.45,
            ),
          ),
        ],
      ),
    );
  }

  // ============================================================
  // SYSTEM
  // ============================================================

  Widget _buildSystemStatus() {
    if (_systemLoading) {
      return _buildLoading('Checking system status...');
    }

    if (_systemError != null) {
      return _buildError(
        title: 'Unable to load system status',
        message: _systemError!,
        onRetry: _loadSystem,
      );
    }

    return RefreshIndicator(
      color: AppTheme.primaryColor,
      backgroundColor: AppTheme.surfaceColor,
      onRefresh: _loadSystem,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
        children: [
          _buildHeader(
            title: 'System Status',
            subtitle: 'CrowdShield infrastructure',
            icon: Icons.settings_suggest_rounded,
          ),
          const SizedBox(height: 18),
          _buildHealthCard(
            title: 'FastAPI Backend',
            status: _systemHealth == null ? 'UNKNOWN' : 'HEALTHY',
            icon: Icons.api_rounded,
          ),
          const SizedBox(height: 12),
          _buildDatabaseCard(),
          const SizedBox(height: 12),
          _buildCameraSystemCard(),
          const SizedBox(height: 16),
          _buildSystemSafetyCard(),
        ],
      ),
    );
  }

  Widget _buildHealthCard({
    required String title,
    required String status,
    required IconData icon,
  }) {
    final healthy = status.toUpperCase() == 'HEALTHY' ||
        status.toUpperCase() == 'OK' ||
        status.toUpperCase() == 'CONNECTED';

    final color =
        healthy ? AppTheme.successColor : AppTheme.warningColor;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surfaceColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: color.withValues(alpha: 0.25),
        ),
      ),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.10),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(
              icon,
              color: color,
            ),
          ),
          const SizedBox(width: 13),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    color: AppTheme.textPrimaryColor,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 3),
                const Text(
                  'Backend service',
                  style: TextStyle(
                    color: AppTheme.textSecondaryColor,
                    fontSize: 11,
                  ),
                ),
              ],
            ),
          ),
          _StatusChip(
            text: status,
            color: color,
          ),
        ],
      ),
    );
  }

  Widget _buildDatabaseCard() {
    final connected = _databaseHealth != null;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surfaceColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppTheme.borderColor,
        ),
      ),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: AppTheme.successColor.withValues(alpha: 0.10),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(
              Icons.storage_rounded,
              color: AppTheme.successColor,
            ),
          ),
          const SizedBox(width: 13),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'SQLite Database',
                  style: TextStyle(
                    color: AppTheme.textPrimaryColor,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                SizedBox(height: 3),
                Text(
                  'Persistent operational data',
                  style: TextStyle(
                    color: AppTheme.textSecondaryColor,
                    fontSize: 11,
                  ),
                ),
              ],
            ),
          ),
          _StatusChip(
            text: connected ? 'HEALTHY' : 'UNKNOWN',
            color: connected
                ? AppTheme.successColor
                : AppTheme.warningColor,
          ),
        ],
      ),
    );
  }

  Widget _buildCameraSystemCard() {
    final count = _cameraResponse?.cameraCount ?? 0;
    final live = _cameraResponse?.liveCameraAvailable ?? false;

    return _SectionCard(
      title: 'Camera System',
      icon: Icons.videocam_rounded,
      child: Column(
        children: [
          _InfoRow(
            label: 'Camera Count',
            value: count,
          ),
          const SizedBox(height: 9),
          _InfoRow(
            label: 'Camera Mode',
            value: live ? 'LIVE' : 'RECORDED REPLAY',
          ),
          const SizedBox(height: 9),
          _InfoRow(
            label: 'Live Camera Available',
            value: live ? 'YES' : 'NO',
          ),
        ],
      ),
    );
  }

  Widget _buildSystemSafetyCard() {
    return _SectionCard(
      title: 'Safety Contract',
      icon: Icons.verified_user_rounded,
      child: Column(
        children: [
          _ControlRow(
            label: 'Human Review',
            value: 'REQUIRED',
            enabled: true,
            color: AppTheme.warningColor,
          ),
          const SizedBox(height: 10),
          _ControlRow(
            label: 'Autonomous Emergency Action',
            value: 'DISABLED',
            enabled: false,
            color: AppTheme.successColor,
          ),
          const SizedBox(height: 10),
          _ControlRow(
            label: 'System Role',
            value: 'DECISION SUPPORT',
            enabled: false,
            color: AppTheme.primaryColor,
          ),
        ],
      ),
    );
  }

  // ============================================================
  // COMMON HELPERS
  // ============================================================

  Widget _buildLoading(String message) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const CircularProgressIndicator(
            color: AppTheme.primaryColor,
          ),
          const SizedBox(height: 16),
          Text(
            message,
            style: const TextStyle(
              color: AppTheme.textSecondaryColor,
              fontSize: 13,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildError({
    required String title,
    required String message,
    required VoidCallback onRetry,
  }) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: _SectionCard(
          title: title,
          icon: Icons.error_outline_rounded,
          child: Column(
            children: [
              Text(
                message,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: AppTheme.textSecondaryColor,
                  fontSize: 12,
                  height: 1.5,
                ),
              ),
              const SizedBox(height: 18),
              ElevatedButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh_rounded),
                label: const Text('Retry'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildEmptyState({
    required IconData icon,
    required String title,
    required String message,
  }) {
    return Container(
      padding: const EdgeInsets.all(30),
      decoration: BoxDecoration(
        color: AppTheme.surfaceColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppTheme.borderColor,
        ),
      ),
      child: Column(
        children: [
          Icon(
            icon,
            color: AppTheme.textSecondaryColor,
            size: 42,
          ),
          const SizedBox(height: 14),
          Text(
            title,
            style: const TextStyle(
              color: AppTheme.textPrimaryColor,
              fontSize: 16,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 7),
          Text(
            message,
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: AppTheme.textSecondaryColor,
              fontSize: 12,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDisclaimerCard({
    required String title,
    required String text,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surfaceColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppTheme.borderColor,
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(
            Icons.info_outline_rounded,
            color: AppTheme.primaryColor,
            size: 21,
          ),
          const SizedBox(width: 11),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    color: AppTheme.textPrimaryColor,
                    fontWeight: FontWeight.w700,
                    fontSize: 13,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  text,
                  style: const TextStyle(
                    color: AppTheme.textSecondaryColor,
                    fontSize: 11,
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

  String _text(dynamic value) {
    if (value == null) return '--';
    return value.toString();
  }

  int _count(dynamic value) {
    if (value is num) return value.toInt().clamp(0, 1 << 31).toInt();
    final parsed = int.tryParse(value?.toString() ?? '') ?? 0;
    return parsed.clamp(0, 1 << 31).toInt();
  }

  double _number(dynamic value) {
    if (value is num) {
      return value.toDouble();
    }

    return double.tryParse(
          value?.toString() ?? '',
        ) ??
        0.0;
  }

  Color _riskColor(String level) {
    switch (level.toUpperCase()) {
      case 'LOW':
        return AppTheme.successColor;
      case 'MODERATE':
        return AppTheme.warningColor;
      case 'HIGH':
        return AppTheme.dangerColor;
      case 'CRITICAL':
        return AppTheme.criticalColor;
      default:
        return AppTheme.primaryColor;
    }
  }

  Color _priorityColor(String value) {
    final upper = value.toUpperCase();

    if (upper.contains('CRITICAL')) {
      return AppTheme.criticalColor;
    }

    if (upper.contains('HIGH')) {
      return AppTheme.dangerColor;
    }

    if (upper.contains('PREPARE') ||
        upper.contains('ACTIVE')) {
      return AppTheme.warningColor;
    }

    if (upper.contains('WATCH')) {
      return AppTheme.primaryColor;
    }

    return AppTheme.successColor;
  }
}

// ============================================================
// REUSABLE UI COMPONENTS
// ============================================================

class _SectionCard extends StatelessWidget {
  final String title;
  final IconData icon;
  final Widget child;

  const _SectionCard({
    required this.title,
    required this.icon,
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
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                icon,
                color: AppTheme.primaryColor,
                size: 21,
              ),
              const SizedBox(width: 9),
              Expanded(
                child: Text(
                  title,
                  style: const TextStyle(
                    color: AppTheme.textPrimaryColor,
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 15),
          child,
        ],
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;
  final Color color;

  const _StatCard({
    required this.title,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: const BoxConstraints(minHeight: 124),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppTheme.surfaceColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.borderColor),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
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
          const SizedBox(height: 12),
          FittedBox(
            fit: BoxFit.scaleDown,
            alignment: Alignment.centerLeft,
            child: Text(
              value,
              maxLines: 1,
              style: const TextStyle(
                color: AppTheme.textPrimaryColor,
                fontSize: 19,
                fontWeight: FontWeight.w900,
              ),
            ),
          ),
          const SizedBox(height: 4),
          Text(
            title,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              color: AppTheme.textSecondaryColor,
              fontSize: 10,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  final dynamic text;
  final Color color;

  const _StatusChip({
    required this.text,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: 9,
        vertical: 5,
      ),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: color.withValues(alpha: 0.25),
        ),
      ),
      child: Text(
        text?.toString() ?? '--',
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

class _DistributionRow extends StatelessWidget {
  final dynamic label;
  final dynamic value;
  final int total;
  final Color color;

  const _DistributionRow({
    required this.label,
    required this.value,
    required this.color,
    this.total = 0,
  });

  @override
  Widget build(BuildContext context) {
    final count = value is num ? value.toInt().clamp(0, 1 << 31) : int.tryParse(value?.toString() ?? '') ?? 0;
    final fraction = total > 0 ? (count / total).clamp(0.0, 1.0) : 0.0;
    final percent = (fraction * 100).toStringAsFixed(0);

    return Padding(
      padding: const EdgeInsets.only(bottom: 15),
      child: Column(
        children: [
          Row(
            children: [
              Container(
                width: 8,
                height: 8,
                decoration: BoxDecoration(color: color, shape: BoxShape.circle),
              ),
              const SizedBox(width: 9),
              Expanded(
                child: Text(
                  label?.toString() ?? '--',
                  style: const TextStyle(
                    color: AppTheme.textSecondaryColor,
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
              Text(
                '$count${total > 0 ? '  ·  $percent%' : ''}',
                style: const TextStyle(
                  color: AppTheme.textPrimaryColor,
                  fontSize: 12,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          ClipRRect(
            borderRadius: BorderRadius.circular(20),
            child: LinearProgressIndicator(
              value: fraction,
              minHeight: 5,
              backgroundColor: AppTheme.borderColor,
              valueColor: AlwaysStoppedAnimation<Color>(color),
            ),
          ),
        ],
      ),
    );
  }
}

class _ControlRow extends StatelessWidget {
  final String label;
  final dynamic value;
  final bool enabled;
  final Color color;

  const _ControlRow({
    required this.label,
    required this.value,
    required this.enabled,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(
          enabled
              ? Icons.warning_amber_rounded
              : Icons.check_circle_outline_rounded,
          color: color,
          size: 20,
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            label,
            style: const TextStyle(
              color: AppTheme.textSecondaryColor,
              fontSize: 12,
            ),
          ),
        ),
        Text(
          value?.toString() ?? '--',
          style: TextStyle(
            color: color,
            fontSize: 10,
            fontWeight: FontWeight.w800,
          ),
        ),
      ],
    );
  }
}

class _InfoRow extends StatelessWidget {
  final dynamic label;
  final dynamic value;

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
          child: Text(
            label?.toString() ?? '--',
            style: const TextStyle(
              color: AppTheme.textSecondaryColor,
              fontSize: 11,
            ),
          ),
        ),
        const SizedBox(width: 12),
        Flexible(
          child: Text(
            value?.toString() ?? '--',
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

class _SmallValue extends StatelessWidget {
  final dynamic label;
  final dynamic value;
  final Color color;

  const _SmallValue({
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label?.toString() ?? '--',
          style: const TextStyle(
            color: AppTheme.textSecondaryColor,
            fontSize: 10,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          value?.toString() ?? '--',
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: TextStyle(
            color: color,
            fontSize: 14,
            fontWeight: FontWeight.w800,
          ),
        ),
      ],
    );
  }
}

class _SignalChip extends StatelessWidget {
  final dynamic text;

  const _SignalChip({
    required this.text,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: 10,
        vertical: 7,
      ),
      decoration: BoxDecoration(
        color: AppTheme.surfaceLightColor,
        borderRadius: BorderRadius.circular(9),
      ),
      child: Text(
        text?.toString() ?? '--',
        maxLines: 2,
        overflow: TextOverflow.ellipsis,
        style: const TextStyle(
          color: AppTheme.textSecondaryColor,
          fontSize: 10,
        ),
      ),
    );
  }
}

class _DisclaimerCard extends StatelessWidget {
  final String text;

  const _DisclaimerCard({
    required this.text,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(15),
      decoration: BoxDecoration(
        color: AppTheme.surfaceColor,
        borderRadius: BorderRadius.circular(15),
        border: Border.all(
          color: AppTheme.borderColor,
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(
            Icons.info_outline_rounded,
            color: AppTheme.primaryColor,
            size: 20,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              text,
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
}