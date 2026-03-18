from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import connection
from apps.categories.models import Category
from apps.tools.models import Tool
from apps.loans.models import Loan, LoanItem
from datetime import date, timedelta

User = get_user_model()

class BusinessLogicTest(TransactionTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Load trigger ke test database — tanpa ini trigger tidak ada
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS trg_decrease_stock_on_approve
                AFTER UPDATE ON loans
                FOR EACH ROW
                BEGIN
                    DECLARE v_tool_id   INT UNSIGNED;
                    DECLARE v_qty       INT UNSIGNED;
                    DECLARE v_stock     INT UNSIGNED;
                    DECLARE v_tool_name VARCHAR(150);
                    DECLARE v_done      TINYINT DEFAULT 0;
                    DECLARE v_msg       VARCHAR(255);

                    DECLARE cur_items CURSOR FOR
                        SELECT tool_id, quantity
                        FROM   loan_items
                        WHERE  loan_id = NEW.id;

                    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = 1;

                    IF OLD.status != 'approved' AND NEW.status = 'approved' THEN
                        OPEN cur_items;
                        validate_loop: LOOP
                            FETCH cur_items INTO v_tool_id, v_qty;
                            IF v_done THEN LEAVE validate_loop; END IF;
                            SELECT stock_available, name
                            INTO   v_stock, v_tool_name
                            FROM   tools WHERE id = v_tool_id FOR UPDATE;
                            IF v_stock < v_qty THEN
                                CLOSE cur_items;
                                SET v_msg = CONCAT('Stok ', v_tool_name, ' tidak cukup.');
                                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_msg;
                            END IF;
                        END LOOP validate_loop;
                        CLOSE cur_items;

                        UPDATE tools t
                        INNER JOIN loan_items li ON li.tool_id = t.id
                        SET t.stock_available = t.stock_available - li.quantity
                        WHERE li.loan_id = NEW.id;
                    END IF;
                END
            """)

    def setUp(self):
        self.admin, _ = User.objects.get_or_create(
            username='admin_test',
            defaults={'email': 'admin@test.com', 'role': 'admin', 'is_staff': True}
        )
        self.admin.set_password('password')
        self.admin.save()

        self.siswa, _ = User.objects.get_or_create(
            username='siswa_test',
            defaults={'email': 'siswa@test.com', 'role': 'peminjam'}
        )

        self.cat, _ = Category.objects.get_or_create(name='Test Cat')

        self.tool, _ = Tool.objects.get_or_create(
            name='Tool Test',
            defaults={
                'category': self.cat,
                'stock_total': 10,
                'stock_available': 10,
                'qr_code': 'test_qr_123'
            }
        )

    def test_stock_decrease_on_approve(self):
        loan = Loan.objects.create(
            user=self.siswa,
            loan_date=date.today(),
            due_date=date.today() + timedelta(days=5),
            status='pending'
        )
        LoanItem.objects.create(loan=loan, tool=self.tool, quantity=3)

        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE loans SET status='approved', approved_by=%s WHERE id=%s",
                [self.admin.id, loan.id]
            )

        self.tool.refresh_from_db()
        self.assertEqual(self.tool.stock_available, 7,
                         "Trigger stok tidak berjalan.")

    def test_fine_calculation_logic(self):
        from core.utils import calculate_fine

        due = date.today() - timedelta(days=5)
        now = date.today()

        res = calculate_fine(due, now, 5000)
        self.assertEqual(res['total_fine'], 25000.00)