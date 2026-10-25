"""Generate the public field catalog and schema without creating runtime data."""
from pathlib import Path
import html
import json

ROOT = Path(__file__).resolve().parent


def field(key, label, kind='text', note='', options=None, more=False, when=None, target=None):
    item = dict(key=key, label=label, type=kind, required=False, nullable=True,
                default=None, note=note, display='展开项' if more else '常用项')
    if options is not None:
        item['options'] = options.split('|') if isinstance(options, str) else options
    if when:
        item['show_when'] = when
    if target:
        item['references'] = target
    return item


def enum(key, label, options, note='', more=False, when=None):
    return field(key, label, 'choice', note, options, more, when)


def ref(key, label, target, multiple=False, note='', more=False):
    return field(key, label, 'references' if multiple else 'reference', note,
                 more=more, target=target)


def module(key, name, purpose, timing, fields, summary):
    return dict(key=key, name=name, purpose=purpose, update_timing=timing,
                fields=fields, list_fields=summary)


COMMON = [
    enum('information_source', '资料来源', '家庭共同讨论|本人陈述|银行或机构记录|合同或协议|保单|账单或报价|其他'),
    field('source_note', '来源补充说明', note='例如材料名称、口头说明人或数据查询位置。', more=True),
    enum('verification_status', '核实状态', '已核实|估算|待确认', '允许暂不选择；不根据是否有附件自动认定已核实。'),
    field('last_confirmed_on', '最后确认日期', 'partial_date', '与资产或债务金额本身的截至日期分开。'),
    field('attachments', '相关资料附件', 'attachment_list', '支持图片、PDF、合同、保单、截图等；附件可不添加。'),
    field('notes', '补充说明', 'long_text'),
]

ALLOCATION = [
    ref('member_id', '承担人', 'members'),
    field('amount', '承担金额', 'money'),
    field('percentage', '承担比例', 'percentage'),
    field('agreement_note', '分担说明', 'long_text', '只填成员和文字约定也可以；不自动平均分摊。'),
]

MONEY_RANGE = [
    field('value', '单一金额', 'money', '单一金额模式下填写；不与范围重复统计。'),
    field('lower', '范围下限', 'money', '缺少下限时保留未知。'),
    field('upper', '范围上限', 'money', '缺少上限时保留未知。'),
]

ATTACHMENT_INFO = [
    field('display_name', '资料展示名称', note='可以使用原文件名的展示值。'),
    field('material_date', '资料日期', 'partial_date'),
    field('material_note', '资料说明', 'long_text'),
]

MODULES = [
    module('members', '家庭成员', '记录家庭成员，提供可编辑的角色模板并支持新增成员。', '首次整理；基本情况变化时更新。', [
        field('display_name', '称呼'),
        enum('family_role', '家庭角色', '本人|父亲|母亲|其他'),
        field('birth_year', '出生年份', 'year', more=True),
        field('living_region', '常住地区', note='城市或地区即可。', more=True),
        enum('work_status', '工作或退休状态', '在职|退休|经营或灵活就业|暂未就业|其他', more=True),
        field('expected_retirement_on', '预计退休时间', 'partial_date', more=True),
    ], ['display_name', 'family_role', 'work_status']),

    module('assets', '资产盘点', '一项资产一条记录；共同资产在家庭内只登记一次。', '首次盘点；重大变化时更新，不要求每月盘点。', [
        field('asset_name', '资产名称或别名'),
        enum('asset_category', '资产类别', '现金|银行活期|定期存款|理财|基金|股票|债券|公积金|房产|车辆|其他'),
        ref('owner_ids', '所有人', 'members', True),
        field('ownership_note', '共有份额说明', 'long_text', '份额不清楚时只写共同所有；个人汇总不默认平分。', more=True),
        field('institution_or_location', '机构或位置', note='银行、平台名称，或房产所在区域等。'),
        field('account_alias', '账户别名', note='用于分组辨认，例如某银行工资卡；不要求完整账号。', more=True),
        field('value', '当前金额或估值', 'money_or_range', '填写本家庭实际持有部分的价值；允许填范围。'),
        field('currency', '币种', 'currency', '不填时不假定币种；不同币种分别汇总。'),
        field('value_as_of', '金额或估值截至日期', 'partial_date'),
        enum('valuation_basis', '金额依据', '账户或机构记录|市场估值|购入金额|本人估算|其他', more=True),
        field('acquisition_cost', '购入成本或投入本金', 'money', '已有信息时选填，不要求补历史交易。', more=True),
        field('maturity_on', '到期时间', 'partial_date', more=True),
        enum('availability', '可动用情况', '可随时动用|到期后可用|需要赎回或出售|受到限制|待确认'),
        field('availability_note', '变现或使用条件', 'long_text', more=True),
        field('designated_use', '已有指定用途', 'long_text', '文字说明即可，不关联重大事项的预留资金。', more=True),
    ], ['asset_name', 'owner_ids', 'value', 'currency', 'value_as_of', 'availability']),

    module('liabilities', '负债与借款', '银行贷款、分期、信用欠款和亲友借款统一逐笔登记。房贷采用概况加还款规则。', '首次盘点；还款安排、利率、期限、承担人或余额有重大变化时更新。', [
        field('liability_name', '负债名称'),
        enum('liability_type', '负债类别', '房贷|车贷|其他银行贷款|信用卡欠款|消费分期|亲友借款|其他'),
        field('creditor_alias', '债权方或贷款机构'),
        ref('borrower_ids', '借款人', 'members', True),
        ref('payer_ids', '实际承担人', 'members', True),
        enum('counterparty_scope', '往来范围', '家庭外部|家庭内部|待确认', more=True),
        ref('internal_creditor_id', '家庭内部债权人', 'members', more=True),
        field('original_principal', '原借款本金', 'money', '已知时填写，不要求还原历史还款。', more=True),
        field('remaining_principal', '当前剩余本金或欠款余额', 'money'),
        field('currency', '币种', 'currency'),
        field('balance_as_of', '余额截至日期', 'partial_date'),
        field('annual_interest_rate', '年利率', 'percentage', more=True),
        enum('rate_type', '利率类型', '固定|浮动|无息|待确认', more=True),
        field('rate_note', '利率及调整说明', 'long_text', more=True),
        enum('repayment_method', '还款方式', '等额本息|等额本金|到期还本|分期约定|其他|待确认', more=True),
        field('regular_payment', '每期还款额', 'money_or_range'),
        enum('payment_frequency', '还款频率', '每月|每季|每半年|每年|其他', more=True),
        field('payment_schedule', '扣款日或付款约定', note='例如每月20日。'),
        field('remaining_periods', '剩余期数', 'integer', more=True),
        field('maturity_on', '到期或预计还清时间', 'partial_date'),
        field('future_payment_estimate', '未来预计还款总额', 'money_or_range', '按银行计划或已确认约定选填；不直接用剩余本金替代。', more=True),
        field('future_payment_basis', '预计还款依据', 'long_text', more=True),
        field('payer_allocations', '按人分担明细', 'allocation_rows', more=True),
        field('repayment_agreement', '还款及提前还款约定', 'long_text', more=True),
        ref('linked_recurring_rule_id', '关联定期还款规则', 'recurring_rules', more=True),
        ref('linked_commitment_id', '关联家庭约定事项', 'commitments', more=True),
        ref('linked_asset_id', '相关资产', 'assets', more=True),
    ], ['liability_name', 'borrower_ids', 'payer_ids', 'remaining_principal', 'balance_as_of', 'regular_payment', 'maturity_on']),

    module('receivables', '借出款', '记录别人欠家庭成员的钱，与可直接使用的存款分开展示。', '首次盘点；收回、延期或约定变化时更新。', [
        field('receivable_name', '借出款名称'),
        ref('owner_ids', '资金归属人', 'members', True),
        field('debtor_alias', '借款方称呼'),
        enum('counterparty_scope', '往来范围', '家庭外部|家庭内部|待确认', more=True),
        ref('internal_debtor_id', '家庭内部借款人', 'members', more=True),
        field('original_amount', '原借出金额', 'money', more=True),
        field('remaining_amount', '尚未收回金额', 'money'),
        field('currency', '币种', 'currency'),
        field('balance_as_of', '余额截至日期', 'partial_date'),
        field('lent_on', '借出时间', 'partial_date', more=True),
        field('expected_return_on', '预计收回时间', 'partial_date'),
        field('repayment_agreement', '归还或分期约定', 'long_text'),
        field('interest_agreement', '利息约定', 'long_text', more=True),
        enum('collection_status', '回收情况', '正常履约|待约定|延期|存在不确定性|已收回|其他'),
        ref('linked_liability_id', '对应家庭内部欠款', 'liabilities', more=True),
        ref('linked_income_rule_id', '关联约定收款规则', 'recurring_rules', more=True),
    ], ['receivable_name', 'owner_ids', 'debtor_alias', 'remaining_amount', 'expected_return_on', 'collection_status']),

    module('guarantees', '担保责任', '单独展示可能承担的责任，记录已确认的条件和金额。', '首次盘点；责任、期限或触发情况变化时更新。', [
        field('guarantee_name', '担保事项'),
        ref('guarantor_ids', '担保人', 'members', True),
        field('related_party_alias', '被担保方或相关方'),
        field('creditor_alias', '债权方', more=True),
        field('exposure_amount', '可能涉及的金额或范围', 'money_or_range'),
        field('currency', '币种', 'currency'),
        field('trigger_conditions', '可能需要承担费用的条件', 'long_text'),
        field('starts_on', '起始时间', 'partial_date', more=True),
        field('ends_on', '期限或结束时间', 'partial_date'),
        enum('status', '责任状态', '生效中|变化待确认|已解除|待确认'),
        field('responsibility_note', '责任及变化说明', 'long_text', more=True),
        ref('linked_liability_id', '确认形成欠款后的关联记录', 'liabilities', more=True),
        ref('linked_commitment_id', '关联家庭事项', 'commitments', more=True),
    ], ['guarantee_name', 'guarantor_ids', 'exposure_amount', 'ends_on', 'status']),

    module('recurring_rules', '定期收支规则', '维护长期规则，变化时修改；工资、水电、电话费、保费、房贷等统一归集。', '首次建立；金额、频率、起止时间或承担安排变化时更新。', [
        field('rule_name', '项目名称'),
        enum('direction', '收支方向', '收入|支出|家庭内部支持或转账'),
        enum('category', '项目类别', '工资|奖金|养老金|租金|利息或分红|经营收入|水电燃气|电话网络|日常固定费用|房贷|其他还款|医保或保费|其他'),
        ref('income_owner_ids', '收入归属人或转账收款人', 'members', True),
        ref('payer_ids', '支出承担人或转账付款人', 'members', True),
        ref('benefiting_member_ids', '费用涉及或受益成员', 'members', True, more=True),
        field('counterparty_alias', '外部收付款方', more=True),
        field('expected_amount', '每期预计金额或范围', 'money_or_range', '收入以预计到手金额、支出以预计支付金额为口径。'),
        field('currency', '币种', 'currency'),
        enum('frequency', '频率', '每周|每月|每季|每半年|每年|其他'),
        field('schedule_note', '收付款时点', note='例如每月10日、每年一月；不要求精确到某一天。'),
        field('effective_from', '生效时间', 'partial_date'),
        field('effective_until', '结束时间', 'partial_date'),
        enum('status', '规则状态', '生效|暂停|终止|待确认'),
        field('amount_change_note', '浮动或调整说明', 'long_text', more=True),
        field('payer_allocations', '分担金额或比例', 'allocation_rows', more=True),
        field('agreement_note', '约定说明', 'long_text'),
        ref('linked_asset_id', '相关资产', 'assets', more=True),
        ref('linked_liability_id', '相关负债', 'liabilities', more=True),
        ref('linked_commitment_id', '相关家庭约定事项', 'commitments', more=True),
        ref('linked_protection_id', '相关保障记录', 'protection', more=True),
    ], ['rule_name', 'direction', 'income_owner_ids', 'payer_ids', 'expected_amount', 'frequency', 'schedule_note', 'status']),

    module('commitments', '重大及约定事项', '一家人讨论后手动纳入，金额不限；同时容纳已约定和待商讨事项。', '首次整理；形成约定、付款进展或其他重要变化时更新。', [
        field('title', '事项名称'),
        field('purpose', '用途或事项说明', 'long_text'),
        enum('spending_pattern', '开销形式', '一次性|定期|分阶段|贷款还款|其他'),
        ref('involved_member_ids', '涉及成员', 'members', True),
        enum('status', '事项状态', '待商讨|已约定|进行中|已完成|暂停|取消'),
        enum('priority', '家庭优先级', '优先保障|正常安排|有余力再考虑|尚未确定'),
        field('planned_start', '计划发生或开始时间', 'partial_date'),
        field('planned_end', '计划结束时间', 'partial_date', more=True),
        field('timing_note', '时间安排说明', 'long_text', '日期未定时可以只填文字。', more=True),
        field('total_amount', '预计或约定总额', 'money_or_range'),
        enum('total_amount_basis', '总额口径', '初步估算|家庭已约定|合同或报价|实际结算|待确认', more=True),
        field('currency', '币种', 'currency'),
        field('confirmed_paid_amount', '累计已确认支付金额', 'money'),
        field('paid_period_start', '已付金额统计起点', 'partial_date', '可以从本次启用日开始；不要求补历史付款。', more=True),
        field('paid_as_of', '已付金额截至日期', 'partial_date'),
        field('payment_scope_note', '累计付款范围说明', 'long_text', '例如仅含启用后付款，或已包含此前已知付款。', more=True),
        field('remaining_payment', '剩余待付或预计待付金额', 'money_or_range'),
        enum('remaining_payment_basis', '待付金额依据', '同一范围的总额减已付|银行还款计划|家庭估算|其他|待确认', more=True),
        field('reserved_amount', '已预留金额', 'money', '只记录金额，不关联账户或具体资产；不自动从资产余额扣除。'),
        ref('payer_ids', '承担人', 'members', True),
        field('allocations', '各人承担金额或比例', 'allocation_rows', '允许只填承担人或文字约定。', more=True),
        field('external_share_note', '其他人员参与或分担说明', 'long_text', more=True),
        field('agreement_note', '家庭约定说明', 'long_text'),
        ref('linked_recurring_rule_ids', '关联定期收支规则', 'recurring_rules', True, more=True),
        ref('linked_liability_id', '关联贷款或其他负债', 'liabilities', more=True),
    ], ['title', 'total_amount', 'planned_start', 'payer_ids', 'status', 'priority', 'remaining_payment']),

    module('protection', '养老医保及商业保险摘要', '只记录关键保障摘要；缴费和养老金领取关联定期收支规则。', '首次整理；参保、保单、缴费或领取安排发生变化时更新。', [
        field('protection_name', '保障项目名称'),
        enum('protection_type', '保障类别', '养老|医保|商业保险|其他'),
        ref('covered_member_ids', '参保人或被保险人', 'members', True),
        field('provider', '经办机构或保险公司'),
        field('participation_region', '参保或办理地区', more=True),
        enum('status', '当前状态', '在缴|保障有效|领取中|停缴或暂停|已结束|待确认'),
        field('scheme_or_policy_type', '制度或险种名称', note='按已有材料填写具体名称。'),
        field('coverage_summary', '关键保障内容', 'long_text', '按材料或共同确认的摘要填写。'),
        field('starts_on', '生效或起始时间', 'partial_date', more=True),
        field('ends_on', '保障或安排结束时间', 'partial_date'),
        field('contribution_years', '已缴费年限', 'decimal', more=True, when='protection_type == 养老'),
        field('pension_start_on', '已开始或预计开始领取时间', 'partial_date', more=True, when='protection_type == 养老'),
        enum('pension_amount_basis', '养老金金额口径', '当前已领取|机构查询的预计金额|本人估算|待确认', more=True, when='protection_type == 养老'),
        field('pension_amount', '每期养老金金额或范围', 'money_or_range', more=True, when='protection_type == 养老'),
        field('pension_frequency', '养老金领取频率', note='例如每月。', more=True, when='protection_type == 养老'),
        field('medical_participation_note', '医保参保及缴费情况', 'long_text', more=True, when='protection_type == 医保'),
        ref('policyholder_ids', '投保人', 'members', True, more=True),
        ref('premium_payer_ids', '缴费承担人', 'members', True, more=True),
        field('policy_alias', '保单别名或尾号', more=True, when='protection_type == 商业保险'),
        field('insured_amount', '保额或保障额度', 'money_or_range', '保额单独展示，不计入资产金额。', more=True, when='protection_type == 商业保险'),
        field('beneficiary_note', '受益安排说明', 'long_text', more=True, when='protection_type == 商业保险'),
        field('premium_amount', '每期缴费金额或范围', 'money_or_range'),
        field('currency', '币种', 'currency'),
        field('premium_frequency', '缴费频率或周期'),
        field('premium_end_on', '缴费结束时间', 'partial_date', more=True),
        field('next_renewal_on', '下次续保或缴费时间', 'partial_date', more=True),
        field('important_terms_summary', '关键条款摘要', 'long_text', '例如保单明确约定的额度、免赔或限制；不收集病历和照护信息。', more=True, when='protection_type == 商业保险'),
        ref('linked_income_rule_id', '养老金等关联收入规则', 'recurring_rules', more=True),
        ref('linked_expense_rule_id', '缴费关联支出规则', 'recurring_rules', more=True),
    ], ['protection_name', 'covered_member_ids', 'protection_type', 'status', 'ends_on', 'premium_amount']),
]

SPEC = {
    'title': '家庭经济信息收集字段设计', 'version': '1.1',
    'status': '本地应用字段定义；需求和实现说明见项目docs目录',
    'editable_source': 'design/build_field_catalog.py',
    'scope': {
        'participants': '支持多个家庭成员；家人共同商讨，由一位维护者统一录入。',
        'purpose': '盘点家庭家底、定期收支安排、重大和约定开销及承担责任。',
        'maintenance': '一次基础盘点，之后维护长期规则及重大变化。',
        'history_start': '从启用时记录，不要求补录历史收支。',
        'presentation': '清单加逐项详情，常用字段先展示，补充字段展开填写。',
        'all_inputs_optional': True,
        'excluded': [
            '健康与照护的独立信息模块', '每位成员最低保留资金',
            '预留金额与具体资产或账户的来源关联', '强制每月余额盘点',
            '强制零散日常消费逐笔或每月汇总', '贷款逐期本金利息明细',
            '强制实际收付款逐期登记',
        ],
    },
    'input_rules': [
        '全部用户输入字段均可留空，包括名称、金额、成员、日期、状态、关联项和附件。可以保存完全未填的草稿。',
        '空白保存为null；未知不是0。只有明确填写的0才表示零金额。',
        '未命名资产、未命名事项、成员未选择等仅作为界面占位，不写成用户已提供的内容。',
        '日期可只填年份或年月，未确定时可写说明；不补造具体日期。',
        '金额可填单一数值或范围；缺少某个边界时保留缺失，不能当成0。',
        '归属或承担人为多人的，份额允许未知；不默认平均分摊，不默认父母资金可自由调配。',
        '有内容时核对数值、日期、金额范围和比例；发现矛盾可提示，仍允许保存草稿。',
        '部分确认、部分估算的记录，可在备注中分别说明。缺少附件不阻止保存，也不自动认定信息可靠或不可靠。',
        '用户不需要输入技术ID。ID、创建时间、修改时间由未来程序自动维护，不属于必填项。',
        '账户使用别名，不设置密码、验证码、完整证件号码等采集字段。',
        '条件字段按类型展开，已填内容在切换类型时保留；所有字段都可在补充区域查看。',
    ],
    'aggregation_rules': [
        '家底显示截至最近盘点日的资产和债务，不将旧盘点值标成实时余额。',
        '未来收支显示按已收录规则估算的金额，并提示覆盖范围；不称为全家真实结余。',
        '定期规则产生预计收付款，不自动生成已到账、已支付或已还本金事实。',
        '缺少金额、币种、时间或频率导致不能推算的项目，显示待补充并计入未参与统计项目数；不按0计。',
        '不同币种分别汇总，未提供汇率时不转换合并；本版不采集或自动获取汇率。',
        '金额范围保持范围；未知上界不显示为确定总额。不同口径的金额分别列示。',
        '已约定与待商讨事项分开汇总，待商讨金额不自动算作已承诺开销。',
        '累计已付需注明统计起点或范围及截至日期；范围未知时不能直接从总额扣减。',
        '剩余待付只有在总额、已付、币种、统计范围一致且资料足够时才可计算；也允许按银行计划或人工估算填写并标明依据。',
        '已预留与已支付分开。预留只表达用途安排，不是新增支出，也不直接减少盘点资产；未关联来源时不做按账户的资金占用核对。',
        '房贷剩余本金与未来预计本息分别展示，未来还款总额按银行计划或明确约定录入；不把剩余本金当作未来全部付款。',
        '房贷付款进度和分担约定由关联家庭事项统一保存，在贷款详情直接展示；用户填写这些内容时由未来程序建立关联，不要求另建两份记录或输入技术ID。',
        '同一房贷、保单或电话费通过关联复用信息。未来收支以关联定期规则为入口，同一付款不因出现在多个页面重复计入。',
        '持续多年事项不把整个事项总额塞进某一年的预算；缺少时间分配依据时只显示总体需求。',
        '银行账户中的活期余额和各产品分别记录；账户总额由明细汇总，不能再把包含这些明细的总余额重复加为资产。',
        '共同资产家庭合计只算一次；份额未知时个人视图单列共同资产，不把整笔同时归给每个人。',
        '借出款、受限资产、可直接动用资金分别展示；借出款不当作已到账现金。',
        '家庭内部转账、支持和相互借贷保留个人关系，家庭合并视图抵销内部往来；内部范围待确认的记录单独提示。',
        '担保等潜在责任单列，确认形成欠款时关联已建立的债务记录，避免重复累加同一责任金额。',
        '保额不作为资产；保障摘要、保费规则、养老金收入分别关联，避免重复计收支。',
        '各人分担金额和比例均选填；两者都有时不重复计作两份分担，不明部分显示待商议。',
    ],
    'lifecycle_rules': [
        '规则和约定变更时保留生效时间、修改时间和旧版本，变更原因选填；不要求用户逐月新建快照。',
        '暂停、终止或取消改变之后的预计安排，保留已有确认资料及已付统计。',
        '资产或债务金额更新时保留该次金额的截至日期和来源；旧版本供回看，不自动视为另一笔资产或债务。',
        '附件关联具体记录；资料日期、展示名称和说明可选填。正文记录不依赖附件才能保存。',
    ],
    'field_types': {
        'text': '短文字', 'long_text': '多行文字', 'choice': '可不选择的选项',
        'money': '十进制金额；币种单独记录；空白与0不同',
        'money_or_range': '单一金额，或下限/上限范围，所有分量均可留空',
        'currency': '币种文字或选择，不填则保持未确认',
        'partial_date': 'YYYY、YYYY-MM或YYYY-MM-DD；日期范围由起止字段或说明表达',
        'year': '年份', 'integer': '整数', 'decimal': '十进制数',
        'percentage': '百分比；不是默认分担值',
        'reference': '关联一条已有记录，可不关联',
        'references': '关联多个成员或记录，可不选择',
        'allocation_rows': '可选分担行；各子字段同样全部选填',
        'attachment_list': '可选附件集合，文件与原始记录关联',
    },
    'shared_fields': COMMON,
    'nested_schemas': {'allocation_rows': ALLOCATION, 'money_or_range': MONEY_RANGE,
                       'attachment_info': ATTACHMENT_INFO},
    'modules': MODULES,
    'system_fields': [
        {'key': 'id', 'input': False, 'generated': True, 'note': '记录技术标识，未来由程序生成。'},
        {'key': 'created_at', 'input': False, 'generated': True, 'note': '首次保存时间。'},
        {'key': 'updated_at', 'input': False, 'generated': True, 'note': '最近修改时间。'},
    ],
    'implementation_handoff': [
        '本稿定义信息内容与记录口径；本地应用的需求和实现说明见项目docs目录。',
        '未来SQLite中业务输入列和关联均允许NULL；仅技术主键和自动时间戳不需要人工填写。',
        '金额宜采用明确精度的十进制表示，或币种明确后采用最小货币单位整数，不以二进制浮点作为唯一金额值。',
        '多成员、选填分担和附件宜用关联记录保存；不以逗号拼接文本替代需要查询的关联关系。',
        '明细关联不存在时仍可保存草稿；不能引用不存在的已保存对象。',
        '这是字段设计文档，页面中的表格不承担实际录入或保存功能。',
    ],
}


def validate():
    keys = {m['key'] for m in MODULES}
    assert len(keys) == len(MODULES) == 8
    common_keys = {f['key'] for f in COMMON}
    all_fields = COMMON + ALLOCATION + MONEY_RANGE + ATTACHMENT_INFO
    for m in MODULES:
        fields = m['fields']
        ids = {f['key'] for f in fields}
        assert len(ids) == len(fields), m['key']
        assert not ids & common_keys, m['key']
        assert set(m['list_fields']) <= ids
        all_fields.extend(fields)
    for f in all_fields:
        assert f['required'] is False and f['nullable'] is True and f['default'] is None, f['key']
        assert f['type'] in SPEC['field_types'], f['type']
        if 'references' in f:
            assert f['references'] in keys, f['references']
    assert 'reserved_asset_id' not in {f['key'] for f in all_fields}
    return len(all_fields)


def esc(value):
    return html.escape(str(value), quote=True)


def bullets(items):
    return '<ul>' + ''.join('<li>' + esc(x) + '</li>' for x in items) + '</ul>'


def field_table(fields):
    rows = []
    for f in fields:
        notes = f['note']
        if f.get('options'):
            notes += ('；' if notes else '') + '选项：' + '、'.join(f['options'])
        if f.get('references'):
            notes += ('；' if notes else '') + '关联：' + next(m['name'] for m in MODULES if m['key'] == f['references'])
        if f.get('show_when'):
            notes += ('；' if notes else '') + '适用条件：' + f['show_when']
        rows.append('<tr><td><strong>' + esc(f['label']) + '</strong><code>' + esc(f['key']) +
                    '</code></td><td>' + esc(SPEC['field_types'][f['type']]) +
                    '</td><td><span class="pill">选填</span><br>' + esc(f['display']) +
                    '</td><td>' + esc(notes or '可按已知信息填写，也可留空。') + '</td></tr>')
    return '<div class="tablewrap"><table><thead><tr><th>字段</th><th>填写方式</th><th>填写要求</th><th>说明</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>'


def render():
    count = validate()
    spec_path = ROOT / '家庭经济信息收集字段定义.json'
    spec_path.write_text(json.dumps(SPEC, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    nav = ''.join('<a href="#' + esc(m['key']) + '">' + esc(m['name']) + '</a>' for m in MODULES)
    parts = ['''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>家庭经济信息收集字段设计</title>
<style>
:root{color-scheme:light;--ink:#182c3c;--muted:#596c79;--accent:#126c69;--line:#dbe4e8;--paper:#fff;--back:#f3f6f7}
*{box-sizing:border-box}body{margin:0;background:var(--back);color:var(--ink);font:15px/1.8 "Microsoft YaHei","Segoe UI",sans-serif}
main{max-width:1180px;margin:auto;padding:36px 28px 80px}header{border-top:5px solid var(--accent);background:var(--paper);padding:28px 32px;border-radius:0 0 12px 12px}
h1{font-size:30px;line-height:1.4;margin:8px 0 16px}h2{font-size:23px;margin:0 0 12px}h3{font-size:17px;margin:24px 0 10px}p{margin:10px 0}.meta{color:var(--muted);font-size:13px;letter-spacing:.05em}.lead{font-size:17px;max-width:950px}
nav{display:flex;gap:8px;flex-wrap:wrap;margin:20px 0}nav a{background:#fff;border:1px solid var(--line);border-radius:7px;padding:5px 12px;color:var(--accent);text-decoration:none}nav a:hover{background:#e4f1ef}
section{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:26px 28px;margin:20px 0;scroll-margin-top:20px}.notice{background:#edf7f4;border-left:4px solid var(--accent);padding:14px 18px;border-radius:4px}.muted{color:var(--muted)}
.tablewrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px;margin:16px 0}th{text-align:left;background:#edf3f5;color:#355363;font-weight:600}th,td{padding:11px 13px;border-bottom:1px solid var(--line);vertical-align:top}th:first-child{width:22%}th:nth-child(2){width:23%}th:nth-child(3){width:12%}th:nth-child(4){width:43%}code{display:block;font:11px/1.6 Consolas,monospace;color:#6b7e8b;overflow-wrap:anywhere;margin-top:4px}.pill{display:inline-block;font-size:12px;color:#126c69;background:#e7f3f0;padding:0 8px;border-radius:12px}ul{padding-left:24px}li{margin:7px 0}a{color:var(--accent)}details{margin-top:15px;border:1px solid var(--line);border-radius:8px;padding:10px 16px}summary{cursor:pointer;color:var(--accent);font-weight:600}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.box{border:1px solid var(--line);border-radius:8px;padding:16px}footer{color:var(--muted);font-size:13px;padding:12px 0}
@media(max-width:760px){main{padding:15px 12px 45px}header,section{padding:20px 16px}h1{font-size:25px}.grid{grid-template-columns:1fr}table{min-width:680px}}
@media print{body{background:#fff;font-size:10pt}main{max-width:none;padding:0}nav,.no-print{display:none}header,section{border-radius:0;border:0;padding:14px 0;margin:0 0 12px}h2,h3{break-after:avoid}thead{display:table-header-group}tr{break-inside:avoid}table{font-size:9pt;min-width:0}.tablewrap{overflow:visible}.grid{display:block}details{display:block}code{font-size:8pt}}
</style></head><body><main><header><div class="meta">家庭一览 · 字段设计 1.1</div>
<h1>家庭经济信息收集字段设计</h1><p class="lead">家人共同商讨，由一位维护者统一录入。首次盘点家庭家底，之后维护定期收支规则与重大约定事项；所有用户输入字段均可留空。</p>
<p class="muted">本页是字段设计说明，不包含实际家庭数据。本地页面和SQLite服务使用同一份结构化字段定义。</p>
<p><a href="家庭经济信息收集字段定义.json">查看结构化字段定义 JSON</a></p></header>''']
    parts.append('<nav>' + nav + '<a href="#common">通用字段</a><a href="#rules">填写与汇总口径</a></nav>')
    parts.append('<section id="overview"><h2>填写和维护方式</h2><div class="notice">名称、金额、成员、日期、状态和附件全部选填。空白是尚未提供；只有明确填写的0才表示零金额。未命名记录也可以保存草稿。</div>')
    parts.append('<div class="grid"><div class="box"><h3>首次整理</h3><p>成员、逐项资产、负债、借出款、担保、保障摘要、定期收支规则、重大或约定事项。历史收支从启用时开始，不要求补录。</p></div><div class="box"><h3>后续维护</h3><p>收入或费用规则、重大事项进展和重要变更发生时更新。家底显示最近盘点日期，收支预测显示依据和覆盖范围。</p></div></div>')
    parts.append('<h3>事项清单与详情分区</h3><p>清单查看事项、金额、时间、承担人、状态及优先级。单项详情分为基本情况、金额与付款进度、承担与约定、资料与确认四区。常用字段先展示，补充字段展开查看，两类都可留空。</p>')
    parts.append('<details><summary>本轮暂不纳入的内容</summary>' + bullets(SPEC['scope']['excluded']) + '</details></section>')
    for m in MODULES:
        labels = {f['key']: f['label'] for f in m['fields']}
        parts.append('<section id="' + esc(m['key']) + '"><h2>' + esc(m['name']) + '</h2><p>' + esc(m['purpose']) + '</p><p class="muted">维护时机：' + esc(m['update_timing']) + '</p>')
        parts.append('<p><strong>清单列：</strong>' + '、'.join(esc(labels[k]) for k in m['list_fields']) + '。可按展示需要调整。</p>')
        if m['key'] == 'commitments':
            parts.append('<div class="notice">重大或约定事项由家人手动指定，不设金额门槛。预留金额只记录数额，不要求关联资金来源。已付金额按已知累计数更新，不要求逐笔录流水。</div>')
        parts.append(field_table(m['fields']))
        parts.append('<p class="muted">另可填写下方的通用资料与确认字段。</p></section>')
    parts.append('<section id="common"><h2>通用资料与确认字段</h2><p>八类记录均支持以下字段，每项都可留空。</p>' + field_table(COMMON) + '<h3>选填的分担明细</h3><p>按需增加成员行，金额和比例均可留空。仅填写“共同承担，具体待商讨”等文字也可以。</p>' + field_table(ALLOCATION) + '<details><summary>金额范围和附件的补充字段</summary><h3>金额或范围</h3>' + field_table(MONEY_RANGE) + '<h3>附件资料说明</h3>' + field_table(ATTACHMENT_INFO) + '<p>原始文件名、文件类型、存放位置和文件大小等由未来程序读取维护，不需要人工填写。</p></details></section>')
    parts.append('<section id="rules"><h2>填写与汇总口径</h2><h3>输入规则</h3>' + bullets(SPEC['input_rules']) + '<h3>金额与统计</h3>' + bullets(SPEC['aggregation_rules']) + '<h3>记录变化</h3>' + bullets(SPEC['lifecycle_rules']) + '</section>')
    parts.append('<section><h2>页面与数据库实现说明</h2>' + bullets(SPEC['implementation_handoff']) + '</section>')
    parts.append('<footer>本设计包含8个信息模块、' + str(count) + '个字段定义（含通用字段、分担子字段、金额范围与附件说明）；全部用户输入字段选填。字段数量不代表需要一次填完的项目数量，通用字段按记录复用。</footer></main></body></html>')
    html_path = ROOT / '家庭经济信息收集字段设计.html'
    html_path.write_text('\n'.join(parts), encoding='utf-8')
    parsed = json.loads(spec_path.read_text(encoding='utf-8'))
    assert parsed['scope']['all_inputs_optional'] is True
    rendered = html_path.read_text(encoding='utf-8')
    assert '<form' not in rendered and '<input' not in rendered
    for m in MODULES:
        assert 'id="' + m['key'] + '"' in rendered
        for f in m['fields']:
            assert '<code>' + f['key'] + '</code>' in rendered
    print(json.dumps({'modules': len(MODULES), 'field_definitions': count,
                      'all_user_fields_optional': True, 'files': [str(html_path), str(spec_path)],
                      'actual_records_created': 0, 'database_created': False}, ensure_ascii=False))


if __name__ == '__main__':
    render()
