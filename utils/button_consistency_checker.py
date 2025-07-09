"""
🔍 Button Consistency Checker
Validates button patterns and ensures design consistency across the bot
"""

import re
import ast
from typing import Dict, List, Set, Tuple
from pathlib import Path


class ButtonConsistencyChecker:
    """Validates button consistency across the codebase."""
    
    # Standard emoji patterns
    EMOJI_PATTERNS = {
        'data_analytics': ['📊', '📚', '📅'],
        'user_management': ['👤', '🔍', '🗑️'],
        'tools_utilities': ['🧮', '🛠️', '🔧'],
        'communication': ['📞', '💬', '📢'],
        'control_navigation': ['🎛️', '⚙️', '🔙', '❌', '🚪'],
        'actions_status': ['🔄', '✅', '💾'],
        'security_privacy': ['🔒', '👁️'],
        'testing_debug': ['🧪']
    }
    
    # Expected button text patterns in Arabic
    ARABIC_PATTERNS = {
        'grades': ['درجات', 'الدرجات'],
        'profile': ['معلوماتي', 'الملف الشخصي'],
        'settings': ['الإعدادات', 'التخصيص'],
        'support': ['الدعم', 'المساعدة'],
        'admin': ['لوحة التحكم', 'الإدارية'],
        'cancel': ['إلغاء', 'إلغاء التسجيل'],
        'logout': ['تسجيل الخروج'],
        'back': ['العودة', 'رجوع'],
        'download': ['تحميل', 'تحميل معلوماتي']
    }
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.suggestions = []
    
    def check_keyboard_file(self, file_path: str) -> Dict:
        """Check button consistency in keyboard definitions."""
        issues = []
        warnings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check emoji usage consistency
            emoji_issues = self._check_emoji_consistency(content)
            issues.extend(emoji_issues)
            
            # Check Arabic text patterns
            text_issues = self._check_arabic_patterns(content)
            issues.extend(text_issues)
            
            # Check button grouping
            grouping_issues = self._check_button_grouping(content)
            warnings.extend(grouping_issues)
            
            # Check callback data patterns
            callback_issues = self._check_callback_patterns(content)
            issues.extend(callback_issues)
            
        except Exception as e:
            issues.append(f"Error reading file {file_path}: {str(e)}")
        
        return {
            'file': file_path,
            'issues': issues,
            'warnings': warnings
        }
    
    def check_handler_file(self, file_path: str) -> Dict:
        """Check button handler consistency in core files."""
        issues = []
        warnings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check handler patterns
            handler_issues = self._check_handler_patterns(content)
            issues.extend(handler_issues)
            
            # Check callback query handling
            callback_issues = self._check_callback_handlers(content)
            issues.extend(callback_issues)
            
            # Check message handler patterns
            message_issues = self._check_message_handlers(content)
            warnings.extend(message_issues)
            
        except Exception as e:
            issues.append(f"Error reading file {file_path}: {str(e)}")
        
        return {
            'file': file_path,
            'issues': issues,
            'warnings': warnings
        }
    
    def _check_emoji_consistency(self, content: str) -> List[str]:
        """Check if emojis are used consistently."""
        issues = []
        
        # Find all emojis in the content
        emoji_pattern = re.compile(r'[📊📚📅👤🔍🗑️🧮🛠️🔧📞💬📢🎛️⚙️🔙❌🚪🔄✅💾🔒👁️🧪]')
        emojis = emoji_pattern.findall(content)
        
        # Check for inconsistent emoji usage
        for emoji in set(emojis):
            # Check if emoji is used in appropriate context
            context_issues = self._check_emoji_context(content, emoji)
            issues.extend(context_issues)
        
        return issues
    
    def _check_emoji_context(self, content: str, emoji: str) -> List[str]:
        """Check if emoji is used in appropriate context."""
        issues = []
        
        # Define expected contexts for each emoji
        context_rules = {
            '📊': ['درجات', 'التحليل', 'الإحصائيات'],
            '📚': ['درجات', 'الفصل', 'المواد'],
            '👤': ['معلوماتي', 'الملف', 'الشخصية'],
            '🔍': ['بحث', 'البحث'],
            '🗑️': ['حذف', 'إزالة'],
            '🧮': ['حساب', 'المعدل'],
            '🛠️': ['فحص', 'إصلاح'],
            '📞': ['الدعم', 'المساعدة'],
            '💬': ['رسالة', 'حكمة'],
            '🎛️': ['لوحة التحكم', 'الإدارية'],
            '⚙️': ['الإعدادات', 'التخصيص'],
            '🔙': ['العودة', 'رجوع'],
            '❌': ['إلغاء'],
            '🚪': ['تسجيل الخروج'],
            '🔄': ['تحديث', 'إعادة'],
            '✅': ['تأكيد'],
            '💾': ['نسخة احتياطية', 'حفظ'],
            '🧪': ['اختبار']
        }
        
        if emoji in context_rules:
            expected_contexts = context_rules[emoji]
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                if emoji in line:
                    # Check if any expected context is present
                    has_context = any(context in line for context in expected_contexts)
                    if not has_context:
                        issues.append(f"Emoji {emoji} used without expected context on line {i+1}")
        
        return issues
    
    def _check_arabic_patterns(self, content: str) -> List[str]:
        """Check Arabic text patterns for consistency."""
        issues = []
        
        # Check for consistent Arabic terminology
        for pattern_name, patterns in self.ARABIC_PATTERNS.items():
            found_patterns = []
            for pattern in patterns:
                if pattern in content:
                    found_patterns.append(pattern)
            
            if len(found_patterns) > 1:
                issues.append(f"Multiple patterns found for {pattern_name}: {found_patterns}")
        
        return issues
    
    def _check_button_grouping(self, content: str) -> List[str]:
        """Check button grouping and layout consistency."""
        warnings = []
        
        # Check for more than 3 buttons per row
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if '[' in line and ']' in line:
                button_count = line.count('[')
                if button_count > 3:
                    warnings.append(f"More than 3 buttons in row on line {i+1}: {button_count} buttons")
        
        return warnings
    
    def _check_callback_patterns(self, content: str) -> List[str]:
        """Check callback data patterns for consistency."""
        issues = []
        
        # Find callback data patterns
        callback_pattern = re.compile(r'callback_data="([^"]+)"')
        callbacks = callback_pattern.findall(content)
        
        # Check for consistent naming patterns
        for callback in callbacks:
            if ':' in callback:
                # Parameterized callback
                action, param = callback.split(':', 1)
                if not param.strip():
                    issues.append(f"Empty parameter in callback: {callback}")
            else:
                # Simple callback
                if not callback.islower() and '_' not in callback:
                    issues.append(f"Inconsistent callback naming: {callback}")
        
        return issues
    
    def _check_handler_patterns(self, content: str) -> List[str]:
        """Check button handler patterns in core files."""
        issues = []
        
        # Check for proper handler registration
        if 'CallbackQueryHandler' in content:
            if 'self._handle_callback' not in content:
                issues.append("Main callback handler not found")
        
        # Check for proper pattern matching
        pattern_matches = re.findall(r'pattern="([^"]+)"', content)
        for pattern in pattern_matches:
            if pattern.startswith('^') and not pattern.endswith('$'):
                issues.append(f"Incomplete regex pattern: {pattern}")
        
        return issues
    
    def _check_callback_handlers(self, content: str) -> List[str]:
        """Check callback query handler patterns."""
        issues = []
        
        # Check for proper callback query handling
        if 'async def _handle_callback' in content:
            if 'update.callback_query' not in content:
                issues.append("Callback query not properly accessed")
            if 'query.answer()' not in content:
                issues.append("Callback query not answered")
        
        return issues
    
    def _check_message_handlers(self, content: str) -> List[str]:
        """Check message handler patterns."""
        warnings = []
        
        # Check for proper message handling
        if 'MessageHandler' in content:
            if 'filters.TEXT' in content:
                if 'filters.Regex' not in content:
                    warnings.append("Consider using filters.Regex for button text matching")
        
        return warnings
    
    def generate_report(self, results: List[Dict]) -> str:
        """Generate a comprehensive consistency report."""
        report = []
        report.append("# 🔍 Button Consistency Report")
        report.append("")
        
        total_issues = 0
        total_warnings = 0
        
        for result in results:
            report.append(f"## 📁 {result['file']}")
            
            if result['issues']:
                report.append("### ❌ Issues:")
                for issue in result['issues']:
                    report.append(f"- {issue}")
                total_issues += len(result['issues'])
            
            if result['warnings']:
                report.append("### ⚠️ Warnings:")
                for warning in result['warnings']:
                    report.append(f"- {warning}")
                total_warnings += len(result['warnings'])
            
            if not result['issues'] and not result['warnings']:
                report.append("### ✅ No issues found")
            
            report.append("")
        
        report.append(f"## 📊 Summary")
        report.append(f"- Total Issues: {total_issues}")
        report.append(f"- Total Warnings: {total_warnings}")
        report.append(f"- Files Checked: {len(results)}")
        
        if total_issues == 0 and total_warnings == 0:
            report.append("🎉 All button patterns are consistent!")
        elif total_issues == 0:
            report.append("✅ No critical issues found, but some warnings to review.")
        else:
            report.append("⚠️ Issues found that should be addressed.")
        
        return "\n".join(report)
    
    def run_full_check(self, project_path: str) -> str:
        """Run a full consistency check on the project."""
        results = []
        
        # Check keyboard files
        keyboard_files = [
            'utils/keyboards.py',
            'admin/dashboard.py',
            'admin/broadcast.py'
        ]
        
        for file_path in keyboard_files:
            full_path = Path(project_path) / file_path
            if full_path.exists():
                result = self.check_keyboard_file(str(full_path))
                results.append(result)
        
        # Check handler files
        handler_files = [
            'bot/core.py'
        ]
        
        for file_path in handler_files:
            full_path = Path(project_path) / file_path
            if full_path.exists():
                result = self.check_handler_file(str(full_path))
                results.append(result)
        
        return self.generate_report(results)


def main():
    """Run the button consistency checker."""
    checker = ButtonConsistencyChecker()
    
    # Run check on current directory
    import os
    project_path = os.getcwd()
    
    report = checker.run_full_check(project_path)
    
    # Save report to file
    with open('button_consistency_report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("Button consistency check completed!")
    print("Report saved to: button_consistency_report.md")
    print("\n" + report)


if __name__ == "__main__":
    main() 