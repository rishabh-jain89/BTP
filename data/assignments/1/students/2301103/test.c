#include <stdio.h>
#include <stdlib.h>
#include <assert.h>

struct Node {
    int data;
    struct Node *next;
};

typedef struct Node *node;

node createNode(int data) {
    node newNode = (node)malloc(sizeof(struct Node));
    assert(newNode != NULL);
    newNode->data = data;
    newNode->next = NULL;
    return newNode;
}

node addFirst(node head, int data) {
    node newNode = createNode(data);
    newNode->next = head;
    return newNode;
}

node addLast(node head, int data) {
    node newNode = createNode(data);

    if (head == NULL) {
        return newNode;
    }

    node temp = head;
    while (temp->next != NULL) {
        temp = temp->next;
    }

    temp->next = newNode;
    return head;
}

int countNodes(node head) {
    int count = 0;

    while (head != NULL) {
        count++;
        head = head->next;
    }

    return count;
}

void printList(node head) {
    node temp = head;

    while (temp != NULL) {
        printf("%d -> ", temp->data);
        temp = temp->next;
    }

    printf("NULL\n");
}

node removeFirst(node head) {
    if (head == NULL) {
        return NULL;
    }

    node temp = head;
    head = head->next;
    free(temp);

    return head;
}

node removeLast(node head) {
    if (head == NULL) {
        return NULL;
    }

    if (head->next == NULL) {
        free(head);
        return NULL;
    }

    node temp = head;

    while (temp->next->next != NULL) {
        temp = temp->next;
    }

    free(temp->next);
    temp->next = NULL;

    return head;
}

int getElement(node head, int pos, int *status) {
    int index = 0;

    while (head != NULL && index < pos) {
        head = head->next;
        index++;
    }

    if (head == NULL || pos < 0) {
        *status = 0;
        return 0;
    }

    *status = 1;
    return head->data;
}

node setElement(node head, int pos, int data) {
    if (pos < 0) {
        return head;
    }

    int index = 0;
    node temp = head;

    while (temp != NULL && index < pos) {
        temp = temp->next;
        index++;
    }

    if (temp != NULL) {
        temp->data = data;
    }

    return head;
}

node addAtPosition(node head, int pos, int data) {
    if (pos <= 0 || head == NULL) {
        return addFirst(head, data);
    }

    node temp = head;
    int index = 0;

    while (temp->next != NULL && index < pos - 1) {
        temp = temp->next;
        index++;
    }

    node newNode = createNode(data);
    newNode->next = temp->next;
    temp->next = newNode;

    return head;
}

node removeAtPosition(node head, int pos) {
    if (head == NULL || pos < 0) {
        return head;
    }

    if (pos == 0) {
        return removeFirst(head);
    }

    node temp = head;
    int index = 0;

    while (temp->next != NULL && index < pos - 1) {
        temp = temp->next;
        index++;
    }

    if (temp->next != NULL) {
        node del = temp->next;
        temp->next = del->next;
        free(del);
    }

    return head;
}

node addAfterKey(node head, int key, int data) {
    node temp = head;

    while (temp != NULL) {
        if (temp->data == key) {
            node newNode = createNode(data);
            newNode->next = temp->next;
            temp->next = newNode;
            return head;
        }

        temp = temp->next;
    }

    return head;
}

node removeFirstOccurrence(node head, int key) {
    if (head == NULL) {
        return NULL;
    }

    if (head->data == key) {
        node temp = head;
        head = head->next;
        free(temp);
        return head;
    }

    node temp = head;

    while (temp->next != NULL) {
        if (temp->next->data == key) {
            node del = temp->next;
            temp->next = del->next;
            free(del);
            return head;
        }

        temp = temp->next;
    }

    return head;
}

node reverseIterative(node head) {
    node prev = NULL;
    node curr = head;
    node next = NULL;

    while (curr != NULL) {
        next = curr->next;
        curr->next = prev;
        prev = curr;
        curr = next;
    }

    return prev;
}

node sortedInsert(node head, int data) {
    node newNode = createNode(data);

    if (head == NULL || data <= head->data) {
        newNode->next = head;
        return newNode;
    }

    node temp = head;

    while (temp->next != NULL && temp->next->data < data) {
        temp = temp->next;
    }

    newNode->next = temp->next;
    temp->next = newNode;

    return head;
}

node sortList(node head) {
    node sorted = NULL;
    node curr = head;

    while (curr != NULL) {
        node next = curr->next;
        curr->next = NULL;

        if (sorted == NULL || curr->data <= sorted->data) {
            curr->next = sorted;
            sorted = curr;
        } else {
            node temp = sorted;

            while (temp->next != NULL && temp->next->data < curr->data) {
                temp = temp->next;
            }

            curr->next = temp->next;
            temp->next = curr;
        }

        curr = next;
    }

    return sorted;
}

void printListRec(node head) {
    if (head == NULL) {
        printf("NULL\n");
        return;
    }

    printf("%d -> ", head->data);
    printListRec(head->next);
}

void printListReverseRec(node head) {
    if (head == NULL) {
        return;
    }

    printListReverseRec(head->next);
    printf("%d -> ", head->data);
}

node reverseRecursive(node head) {
    if (head == NULL || head->next == NULL) {
        return head;
    }

    node newHead = reverseRecursive(head->next);
    head->next->next = head;
    head->next = NULL;

    return newHead;
}

void freeList(node head) {
    while (head != NULL) {
        node temp = head;
        head = head->next;
        free(temp);
    }
}

int main() {
    node list = NULL;
    node sorted_list = NULL;

    int n;
    scanf("%d", &n);

    int *arr = NULL;

    if (n > 0) {
        arr = (int *)malloc(n * sizeof(int));
        assert(arr != NULL);

        for (int i = 0; i < n; i++) {
            scanf("%d", &arr[i]);
        }

        for (int i = 0; i < n; i++) {
            list = addLast(list, arr[i]);
        }

        free(arr);
    }

    printf("Original list:\n");
    printList(list);

    printf("Count:\n");
    printf("%d\n", countNodes(list));

    printf("After removing first:\n");
    list = removeFirst(list);
    printList(list);

    int end_value;
    scanf("%d", &end_value);

    printf("After adding at end:\n");
    list = addLast(list, end_value);
    printList(list);

    printf("After removing last:\n");
    list = removeLast(list);
    printList(list);

    int get_pos;
    scanf("%d", &get_pos);

    printf("Element at position:\n");
    int status = 0;
    int element = getElement(list, get_pos, &status);

    if (status) {
        printf("%d\n", element);
    } else {
        printf("Invalid position\n");
    }

    int set_pos, set_value;
    scanf("%d %d", &set_pos, &set_value);

    printf("After setting element:\n");
    list = setElement(list, set_pos, set_value);
    printList(list);

    int add_pos, add_value;
    scanf("%d %d", &add_pos, &add_value);

    printf("After adding element at position:\n");
    list = addAtPosition(list, add_pos, add_value);
    printList(list);

    int remove_pos;
    scanf("%d", &remove_pos);

    printf("After removing element at position:\n");
    list = removeAtPosition(list, remove_pos);
    printList(list);

    int add_key, value_after_key;
    scanf("%d %d", &add_key, &value_after_key);

    printf("After adding after first occurrence:\n");
    list = addAfterKey(list, add_key, value_after_key);
    printList(list);

    int remove_key;
    scanf("%d", &remove_key);

    printf("After removing first occurrence:\n");
    list = removeFirstOccurrence(list, remove_key);
    printList(list);

    printf("After iterative reverse:\n");
    list = reverseIterative(list);
    printList(list);

    printf("After sorting:\n");
    list = sortList(list);
    printList(list);

    printf("Recursive print:\n");
    printListRec(list);

    printf("Recursive reverse print:\n");
    printListReverseRec(list);
    printf("NULL\n");

    printf("After recursive physical reverse:\n");
    list = reverseRecursive(list);
    printList(list);

    int sorted_n;
    scanf("%d", &sorted_n);

    int *sorted_arr = NULL;

    if (sorted_n > 0) {
        sorted_arr = (int *)malloc(sorted_n * sizeof(int));
        assert(sorted_arr != NULL);

        for (int i = 0; i < sorted_n; i++) {
            scanf("%d", &sorted_arr[i]);
        }

        for (int i = 0; i < sorted_n; i++) {
            sorted_list = addLast(sorted_list, sorted_arr[i]);
        }

        free(sorted_arr);
    }

    printf("Sorted list:\n");
    printList(sorted_list);

    int insert_sorted_value;
    scanf("%d", &insert_sorted_value);

    printf("After sorted insertion:\n");
    sorted_list = sortedInsert(sorted_list, insert_sorted_value);
    printList(sorted_list);

    freeList(list);
    freeList(sorted_list);

    return 0;
}