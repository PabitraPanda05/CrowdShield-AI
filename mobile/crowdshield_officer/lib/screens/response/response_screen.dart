import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';
import '../../models/alert_model.dart';
import '../../models/dashboard_model.dart';
import '../../services/api_service.dart';

class ResponseScreen extends StatefulWidget {
  const ResponseScreen({super.key});

  @override
  State<ResponseScreen> createState() => _ResponseScreenState();
}

class _ResponseScreenState extends State<ResponseScreen> {
  final ApiService _apiService = ApiService();

  DashboardModel? _dashboard;
  List<AlertModel> _alerts = [];

  bool _loading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() {
      _loading = true;
      _errorMessage = null;
    });

    try {
      final results = await Future.wait([
        _apiService.getDashboardSummary(),
        _apiService.getAlerts(),
      ]);

      final dashboardJson =
          results[0] as Map<String, dynamic>;

      final alerts =
          results[1] as List<AlertModel>;

      if (!mounted) return;

      setState(() {
        _dashboard =
            DashboardModel.fromJson(dashboardJson);
        _alerts = alerts;
        _loading = false;
      });
    } catch (error) {
      if (!mounted) return;

      setState(() {
        _loading = false;
        _errorMessage = error.toString();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      appBar: AppBar(
        title: const Text('Response'),
        backgroundColor: AppTheme.backgroundColor,
        elevation: 0,
        actions: [
          IconButton(
            onPressed: _loadData,
            icon: const Icon(Icons.refresh),
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

    if (_errorMessage != null) {
      return _ErrorState(
        message: _errorMessage!,
        onRetry: _loadData,
      );
    }

    if (_dashboard == null) {
      return const _EmptyState(
        message: 'No response data available.',
      );
    }

    final latest = _dashboard!.latestState;

    return RefreshIndicator(
      onRefresh: _loadData,
      color: AppTheme.primaryColor,
      backgroundColor: AppTheme.surfaceColor,
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(
          20,
          12,
          20,
          32,
        ),
        children: [
          const _PageHeader(),

          const SizedBox(height: 20),

          _CurrentResponseCard(
            riskLevel: latest.riskLevel,
            riskScore: latest.riskScore,
            responseAction: latest.responseAction,
            priority: latest.responsePriority,
          ),

          const SizedBox(height: 16),

          _SafetyControlsCard(
            humanReviewRequired:
                latest.humanReviewRequired,
            autonomousEmergencyAction:
                latest.autonomousEmergencyAction,
          ),

          const SizedBox(height: 20),

          const _SectionTitle(
            title: 'Latest Operational Decision',
            icon: Icons.rule_rounded,
          ),

          const SizedBox(height: 10),

          if (_alerts.isNotEmpty)
            _LatestDecisionCard(
              alert: _alerts.first,
            )
          else
            const _EmptyState(
              message:
                  'No operational decisions available.',
            ),

          const SizedBox(height: 20),

          const _SectionTitle(
            title: 'Response Distribution',
            icon: Icons.bar_chart_rounded,
          ),

          const SizedBox(height: 10),

          _ResponseDistributionCard(
            distribution:
                _dashboard!.responseDistribution,
          ),

          const SizedBox(height: 20),

          const _SectionTitle(
            title: 'Recent Operational Decisions',
            icon: Icons.history_rounded,
          ),

          const SizedBox(height: 10),

          if (_alerts.isEmpty)
            const _EmptyState(
              message:
                  'No recent response decisions.',
            )
          else
            ..._alerts.take(10).map(
              (alert) => Padding(
                padding:
                    const EdgeInsets.only(bottom: 10),
                child: _RecentDecisionCard(
                  alert: alert,
                ),
              ),
            ),

          const SizedBox(height: 12),

          const _DisclaimerCard(),
        ],
      ),
    );
  }
}

// ================================================================
// PAGE HEADER
// ================================================================

class _PageHeader extends StatelessWidget {
  const _PageHeader();

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment:
          CrossAxisAlignment.start,
      children: [
        Text(
          'Officer Response',
          style: Theme.of(context)
              .textTheme
              .headlineSmall
              ?.copyWith(
                color: AppTheme.textPrimaryColor,
                fontWeight: FontWeight.w800,
              ),
        ),
        const SizedBox(height: 6),
        Text(
          'Operational response guidance from the production risk engine.',
          style: Theme.of(context)
              .textTheme
              .bodyMedium
              ?.copyWith(
                color: AppTheme.textSecondaryColor,
                height: 1.4,
              ),
        ),
      ],
    );
  }
}

// ================================================================
// CURRENT RESPONSE CARD
// ================================================================

class _CurrentResponseCard extends StatelessWidget {
  const _CurrentResponseCard({
    required this.riskLevel,
    required this.riskScore,
    required this.responseAction,
    required this.priority,
  });

  final String riskLevel;
  final double riskScore;
  final String responseAction;
  final String priority;

  Color _riskColor(String level) {
    switch (level.toUpperCase()) {
      case 'CRITICAL':
        return AppTheme.criticalColor;
      case 'HIGH':
        return AppTheme.dangerColor;
      case 'MODERATE':
        return AppTheme.warningColor;
      case 'LOW':
        return AppTheme.successColor;
      default:
        return AppTheme.primaryColor;
    }
  }

  Color _priorityColor(String value) {
    switch (value.toUpperCase()) {
      case 'CRITICAL':
        return AppTheme.criticalColor;
      case 'HIGH':
        return AppTheme.dangerColor;
      case 'MEDIUM':
        return AppTheme.warningColor;
      case 'LOW':
        return AppTheme.successColor;
      default:
        return AppTheme.textSecondaryColor;
    }
  }

  @override
  Widget build(BuildContext context) {
    final riskColor = _riskColor(riskLevel);

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppTheme.surfaceColor,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: riskColor.withValues(alpha: 0.45),
        ),
      ),
      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color:
                      riskColor.withValues(alpha: 0.12),
                  borderRadius:
                      BorderRadius.circular(12),
                ),
                child: Icon(
                  Icons.shield_outlined,
                  color: riskColor,
                ),
              ),
              const SizedBox(width: 12),
              const Expanded(
                child: Text(
                  'Current Response',
                  style: TextStyle(
                    color: AppTheme.textPrimaryColor,
                    fontSize: 17,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
              _Badge(
                text: riskLevel,
                color: riskColor,
              ),
            ],
          ),

          const SizedBox(height: 22),

          Text(
            responseAction,
            style: TextStyle(
              color: riskColor,
              fontSize: 28,
              fontWeight: FontWeight.w800,
            ),
          ),

          const SizedBox(height: 6),

          const Text(
            'Current operational response',
            style: TextStyle(
              color: AppTheme.textSecondaryColor,
              fontSize: 13,
            ),
          ),

          const SizedBox(height: 20),

          Row(
            children: [
              Expanded(
                child: _ResponseMetric(
                  label: 'Risk Score',
                  value: riskScore.toStringAsFixed(2),
                  color: riskColor,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _ResponseMetric(
                  label: 'Priority',
                  value: priority,
                  color: _priorityColor(priority),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ================================================================
// RESPONSE METRIC
// ================================================================

class _ResponseMetric extends StatelessWidget {
  const _ResponseMetric({
    required this.label,
    required this.value,
    required this.color,
  });

  final String label;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppTheme.surfaceLightColor,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: const TextStyle(
              color: AppTheme.textSecondaryColor,
              fontSize: 12,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            value,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              color: color,
              fontSize: 17,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }
}

// ================================================================
// SAFETY CONTROLS
// ================================================================

class _SafetyControlsCard extends StatelessWidget {
  const _SafetyControlsCard({
    required this.humanReviewRequired,
    required this.autonomousEmergencyAction,
  });

  final bool humanReviewRequired;
  final bool autonomousEmergencyAction;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppTheme.surfaceColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppTheme.borderColor,
        ),
      ),
      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [
          const Text(
            'Safety Controls',
            style: TextStyle(
              color: AppTheme.textPrimaryColor,
              fontSize: 16,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 14),
          _SafetyRow(
            icon: Icons.person_outline_rounded,
            label: 'Human Review',
            value: humanReviewRequired
                ? 'REQUIRED'
                : 'NOT REQUIRED',
            color: humanReviewRequired
                ? AppTheme.warningColor
                : AppTheme.successColor,
          ),
          const SizedBox(height: 10),
          _SafetyRow(
            icon: Icons.smart_toy_outlined,
            label:
                'Autonomous Emergency Action',
            value: autonomousEmergencyAction
                ? 'ENABLED'
                : 'DISABLED',
            color: autonomousEmergencyAction
                ? AppTheme.dangerColor
                : AppTheme.successColor,
          ),
        ],
      ),
    );
  }
}

class _SafetyRow extends StatelessWidget {
  const _SafetyRow({
    required this.icon,
    required this.label,
    required this.value,
    required this.color,
  });

  final IconData icon;
  final String label;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(
          icon,
          size: 21,
          color: AppTheme.primaryColor,
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            label,
            style: const TextStyle(
              color: AppTheme.textSecondaryColor,
              fontSize: 13,
            ),
          ),
        ),
        Text(
          value,
          style: TextStyle(
            color: color,
            fontSize: 11,
            fontWeight: FontWeight.w800,
          ),
        ),
      ],
    );
  }
}

// ================================================================
// LATEST OPERATIONAL DECISION
// ================================================================

class _LatestDecisionCard extends StatelessWidget {
  const _LatestDecisionCard({
    required this.alert,
  });

  final AlertModel alert;

  Color _riskColor(String level) {
    switch (level.toUpperCase()) {
      case 'CRITICAL':
        return AppTheme.criticalColor;
      case 'HIGH':
        return AppTheme.dangerColor;
      case 'MODERATE':
        return AppTheme.warningColor;
      case 'LOW':
        return AppTheme.successColor;
      default:
        return AppTheme.primaryColor;
    }
  }

  Color _priorityColor(String priority) {
    switch (priority.toUpperCase()) {
      case 'CRITICAL':
        return AppTheme.criticalColor;
      case 'HIGH':
        return AppTheme.dangerColor;
      case 'MEDIUM':
        return AppTheme.warningColor;
      case 'LOW':
        return AppTheme.successColor;
      default:
        return AppTheme.textSecondaryColor;
    }
  }

  @override
  Widget build(BuildContext context) {
    final riskColor =
        _riskColor(alert.operationalRiskLevel);

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppTheme.surfaceColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppTheme.borderColor,
        ),
      ),
      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  'Window ${alert.windowId}',
                  style: const TextStyle(
                    color: AppTheme.textPrimaryColor,
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
              _Badge(
                text: alert.responsePriority,
                color: _priorityColor(
                  alert.responsePriority,
                ),
              ),
            ],
          ),

          const SizedBox(height: 14),

          _InfoRow(
            label: 'Risk Level',
            value: alert.operationalRiskLevel,
            valueColor: riskColor,
          ),

          _InfoRow(
            label: 'Risk Score',
            value: alert.operationalRiskScore
                .toStringAsFixed(2),
          ),

          _InfoRow(
            label: 'Response',
            value: alert.responseAction,
            valueColor: AppTheme.primaryColor,
          ),

          _InfoRow(
            label: 'Dominant Factor',
            value: alert.dominantRiskFactor,
          ),

          const SizedBox(height: 12),

          const Text(
            'Operational Reason',
            style: TextStyle(
              color: AppTheme.textSecondaryColor,
              fontSize: 12,
            ),
          ),

          const SizedBox(height: 5),

          Text(
            alert.operationalRiskReason.isEmpty
                ? 'No additional reason provided.'
                : alert.operationalRiskReason,
            style: const TextStyle(
              color: AppTheme.textPrimaryColor,
              fontSize: 14,
              height: 1.4,
            ),
          ),

          if (alert.activeSignals.isNotEmpty) ...[
            const SizedBox(height: 14),
            const Text(
              'Active Signals',
              style: TextStyle(
                color: AppTheme.textSecondaryColor,
                fontSize: 12,
              ),
            ),
            const SizedBox(height: 8),
            _SignalChip(
              text: alert.activeSignals,
            ),
          ],
        ],
      ),
    );
  }
}

// ================================================================
// RECENT DECISION
// ================================================================

class _RecentDecisionCard extends StatelessWidget {
  const _RecentDecisionCard({
    required this.alert,
  });

  final AlertModel alert;

  Color _riskColor(String level) {
    switch (level.toUpperCase()) {
      case 'CRITICAL':
        return AppTheme.criticalColor;
      case 'HIGH':
        return AppTheme.dangerColor;
      case 'MODERATE':
        return AppTheme.warningColor;
      case 'LOW':
        return AppTheme.successColor;
      default:
        return AppTheme.primaryColor;
    }
  }

  @override
  Widget build(BuildContext context) {
    final color =
        _riskColor(alert.operationalRiskLevel);

    return Container(
      padding: const EdgeInsets.all(15),
      decoration: BoxDecoration(
        color: AppTheme.surfaceColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: AppTheme.borderColor,
        ),
      ),
      child: Row(
        children: [
          Container(
            width: 7,
            height: 52,
            decoration: BoxDecoration(
              color: color,
              borderRadius: BorderRadius.circular(8),
            ),
          ),
          const SizedBox(width: 13),
          Expanded(
            child: Column(
              crossAxisAlignment:
                  CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        'Window ${alert.windowId}',
                        style: const TextStyle(
                          color:
                              AppTheme.textPrimaryColor,
                          fontWeight:
                              FontWeight.w700,
                        ),
                      ),
                    ),
                    Text(
                      alert.operationalRiskScore
                          .toStringAsFixed(1),
                      style: TextStyle(
                        color: color,
                        fontWeight:
                            FontWeight.w800,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 5),
                Text(
                  '${alert.operationalRiskLevel} • '
                  '${alert.responseAction}',
                  style: const TextStyle(
                    color:
                        AppTheme.textSecondaryColor,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ================================================================
// RESPONSE DISTRIBUTION
// ================================================================

class _ResponseDistributionCard
    extends StatelessWidget {
  const _ResponseDistributionCard({
    required this.distribution,
  });

  final Map<String, int> distribution;

  Color _responseColor(String response) {
    final value = response.toUpperCase();

    if (value.contains('CRITICAL')) {
      return AppTheme.criticalColor;
    }

    if (value.contains('ESCALATED') ||
        value.contains('HIGH')) {
      return AppTheme.dangerColor;
    }

    if (value.contains('ACTIVE') ||
        value.contains('PREPARE')) {
      return AppTheme.warningColor;
    }

    if (value.contains('MONITOR')) {
      return AppTheme.primaryColor;
    }

    return AppTheme.successColor;
  }

  @override
  Widget build(BuildContext context) {
    if (distribution.isEmpty) {
      return const _EmptyState(
        message:
            'No response distribution available.',
      );
    }

    final entries = distribution.entries.toList()
      ..sort(
        (a, b) => b.value.compareTo(a.value),
      );

    final total = distribution.values.fold<int>(
      0,
      (sum, value) => sum + value,
    );

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppTheme.surfaceColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppTheme.borderColor,
        ),
      ),
      child: Column(
        children: entries.map((entry) {
          final ratio =
              total == 0 ? 0.0 : entry.value / total;

          return Padding(
            padding:
                const EdgeInsets.only(bottom: 13),
            child: Column(
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        entry.key,
                        style: const TextStyle(
                          color:
                              AppTheme.textPrimaryColor,
                          fontSize: 13,
                        ),
                      ),
                    ),
                    Text(
                      '${entry.value}',
                      style: const TextStyle(
                        color:
                            AppTheme.textPrimaryColor,
                        fontWeight:
                            FontWeight.w700,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 7),
                ClipRRect(
                  borderRadius:
                      BorderRadius.circular(8),
                  child: LinearProgressIndicator(
                    value: ratio,
                    minHeight: 6,
                    backgroundColor:
                        AppTheme.surfaceLightColor,
                    valueColor:
                        AlwaysStoppedAnimation<Color>(
                      _responseColor(entry.key),
                    ),
                  ),
                ),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }
}

// ================================================================
// SECTION TITLE
// ================================================================

class _SectionTitle extends StatelessWidget {
  const _SectionTitle({
    required this.title,
    required this.icon,
  });

  final String title;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(
          icon,
          size: 20,
          color: AppTheme.primaryColor,
        ),
        const SizedBox(width: 9),
        Text(
          title,
          style: const TextStyle(
            color: AppTheme.textPrimaryColor,
            fontSize: 17,
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
  const _InfoRow({
    required this.label,
    required this.value,
    this.valueColor,
  });

  final String label;
  final String value;
  final Color? valueColor;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 9),
      child: Row(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Text(
              label,
              style: const TextStyle(
                color: AppTheme.textSecondaryColor,
                fontSize: 13,
              ),
            ),
          ),
          const SizedBox(width: 12),
          Flexible(
            child: Text(
              value,
              textAlign: TextAlign.right,
              style: TextStyle(
                color:
                    valueColor ??
                    AppTheme.textPrimaryColor,
                fontSize: 13,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ================================================================
// BADGE
// ================================================================

class _Badge extends StatelessWidget {
  const _Badge({
    required this.text,
    required this.color,
  });

  final String text;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: 10,
        vertical: 6,
      ),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        text,
        style: TextStyle(
          color: color,
          fontSize: 10,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}

// ================================================================
// SIGNAL CHIP
// ================================================================

class _SignalChip extends StatelessWidget {
  const _SignalChip({
    required this.text,
  });

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(
        horizontal: 10,
        vertical: 8,
      ),
      decoration: BoxDecoration(
        color: AppTheme.surfaceLightColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: AppTheme.borderColor,
        ),
      ),
      child: Text(
        text,
        style: const TextStyle(
          color: AppTheme.textSecondaryColor,
          fontSize: 11,
        ),
      ),
    );
  }
}

// ================================================================
// DISCLAIMER
// ================================================================

class _DisclaimerCard extends StatelessWidget {
  const _DisclaimerCard();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(15),
      decoration: BoxDecoration(
        color: AppTheme.surfaceLightColor.withValues(
          alpha: 0.7,
        ),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: AppTheme.borderColor,
        ),
      ),
      child: const Row(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [
          Icon(
            Icons.info_outline_rounded,
            size: 19,
            color: AppTheme.primaryColor,
          ),
          SizedBox(width: 10),
          Expanded(
            child: Text(
              'Response actions are rule-based operational '
              'decision support. They are not autonomous '
              'emergency commands and require human review.',
              style: TextStyle(
                color: AppTheme.textSecondaryColor,
                fontSize: 12,
                height: 1.45,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ================================================================
// ERROR STATE
// ================================================================

class _ErrorState extends StatelessWidget {
  const _ErrorState({
    required this.message,
    required this.onRetry,
  });

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(
              Icons.cloud_off_rounded,
              size: 48,
              color: AppTheme.warningColor,
            ),
            const SizedBox(height: 14),
            const Text(
              'Unable to load response data',
              style: TextStyle(
                color: AppTheme.textPrimaryColor,
                fontSize: 17,
                fontWeight: FontWeight.w700,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              message,
              style: const TextStyle(
                color: AppTheme.textSecondaryColor,
                fontSize: 12,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 18),
            ElevatedButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }
}

// ================================================================
// EMPTY STATE
// ================================================================

class _EmptyState extends StatelessWidget {
  const _EmptyState({
    required this.message,
  });

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppTheme.surfaceColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: AppTheme.borderColor,
        ),
      ),
      child: Row(
        children: [
          const Icon(
            Icons.info_outline_rounded,
            color: AppTheme.textSecondaryColor,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              message,
              style: const TextStyle(
                color: AppTheme.textSecondaryColor,
                fontSize: 13,
              ),
            ),
          ),
        ],
      ),
    );
  }
}